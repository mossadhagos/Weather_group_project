'''Database Connection'''

# importing libraries
import os  #Allows reading environment variables like passwords
import psycopg
from dotenv import load_dotenv #Loads variables from .env file
from datetime import datetime
import pandas as pd
from io import StringIO


#load enviroment variables from .env file
load_dotenv()

csv_file = "data/mockup_data.csv"

def get_connection(): #reuasble connection function
    """
    Creates and returns a database connection.
    """
    

    conn = psycopg.connect(
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT',"5432"),
    )
    return conn

'''Data Ingestion (Load Raw Data)'''


# Store the CSV exactly as received before any cleaning.

def ingest_raw_csv(csv_file):
    """
    Reads a CSV file and stores each line
    into a raw database table.
    """

    conn = get_connection()

    with conn.cursor() as cur:

        # Create raw schema
        cur.execute("""
            CREATE SCHEMA IF NOT EXISTS raw2
        """)

        # Drop table if it exists to avoid column conflicts
        cur.execute("DROP TABLE IF EXISTS raw2.chris_table")


        # Create table for raw CSV lines
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw2.chris_table (
                line TEXT
            )
        """)

        conn.commit()

        # Open CSV file
        with open(csv_file, "r", encoding="utf-8", errors="surrogateescape") as f:

            # COPY is the fastest way to load data(it makes bulk insert also)
            with cur.copy("COPY raw2.chris_table (line) FROM STDIN") as copy:

                for line in f:
                    copy.write_row([line.rstrip("\n")]) #inserts each line

    conn.commit()
    conn.close()


'''Read Raw Data from Database'''

# Now we reconstruct the CSV into a DataFrame.

#import pandas as pd

def load_raw_data():
    """
    Reads raw CSV lines from the database
    and converts them into a pandas dataframe.
    """

    conn = get_connection()
    rows: list = []


    with conn.cursor() as cur:
        cur.execute("SELECT created_at, temp FROM raw2.chris_table")

        for row in cur:
            rows.append(row)

    conn.close()

    df = pd.DataFrame(rows, columns=["created_at", "temp"])
    return df

'''Data Transformation/Cleaning'''

"""
Now we clean the data 
convert data types and format
flag suspicious values/extreme temp and missing dates
reject impossible/invalid values 
separate valid / rejected rows
"""

def clean_weather_data(df):

    # Convert columns
    df['created_at'] = pd.to_datetime(df['created_at'], format="mixed", errors='coerce')

    df['temp'] = pd.to_numeric(
        df['temp'].astype(str)
        .str.replace('"', '', regex=False)
        .str.replace(",", ".", regex=False),
        errors='coerce'
    ).round(1)

    # Remove duplicates FIRST (fix warning)
    df = df.drop_duplicates(subset=["created_at", "temp"]).reset_index(drop=True)

    # Flags
    df["flag_invalid_date"] = df["created_at"].isna()
    df["flag_invalid_temp"] = df["temp"].isna()
    df["flag_extreme_temp"] = df["temp"] >= 100
    df["flag_invalid_timestamp"] = df["created_at"] > pd.Timestamp.now()

    # Reject reason column
    df["reject_reason"] = ""

    df.loc[df["flag_invalid_date"], "reject_reason"] += "invalid_date; "
    df.loc[df["flag_invalid_temp"], "reject_reason"] += "invalid_temp; "
    df.loc[df["flag_extreme_temp"], "reject_reason"] += "extreme_temp; "
    df.loc[df["flag_invalid_timestamp"], "reject_reason"] += "future_date; "

    df["reject_reason"] = df["reject_reason"].str.strip("; ")

    # Split
    reject_condition = df["reject_reason"] != ""

    df_rejected = df[reject_condition].copy()
    df_valid = df[~reject_condition].copy()

    return df_valid, df_rejected


'''Validation & Testing'''

# Save rejected and valid rows 

def save_validation_results(df_valid, df_rejected):

    import os
    os.makedirs("data/output", exist_ok=True)  

    df_rejected.to_csv(
        "data/output/rejected_weather.csv",
        index=False
    )

    df_valid.to_csv(
        "data/output/accepted_weather.csv",
        index=False
    )

'''Load Clean Data into Database'''

# Now we store clean data in a new schema.

def load_clean_data(df_clean):

    conn = get_connection()

    # Keep only needed columns
    df_clean = df_clean[["created_at", "temp"]]

    with conn.cursor() as cur:

        cur.execute("CREATE SCHEMA IF NOT EXISTS clean2")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS clean2.chris_table2 (
                id SERIAL PRIMARY KEY,
                created_at DATE,
                temp FLOAT
            )
        """)

        #Prevent duplicates on rerun
        cur.execute("TRUNCATE clean2.chris_table2")

        conn.commit()

        buffer = StringIO()
        df_clean.to_csv(buffer, index=False, header=False)
        buffer.seek(0)

        with cur.copy(
            "COPY clean2.chris_table2 (created_at, temp) FROM STDIN WITH CSV"
        ) as copy:
            for line in buffer:
                copy.write(line)

    conn.commit()
    conn.close()


'''Main Pipeline'''

# Finally, run everything in order.

if __name__ == "__main__":

    print("Starting ETL pipeline...")

    # Step 1 - Raw data already loaded by init.sql, just read it
    df_raw = load_raw_data()  # reads from raw2.chris_table

    # Step 2 - Transform
    df_valid, df_rejected = clean_weather_data(df_raw)

    # Step 3 - Save validation CSVs
    save_validation_results(df_valid, df_rejected)

    # Step 4 - Load clean data
    load_clean_data(df_valid)

    print("ETL completed successfully")


