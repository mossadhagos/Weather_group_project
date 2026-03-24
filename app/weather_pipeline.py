'''Database Connection'''

# importing libraries
import os  #Allows reading environment variables like passwords
import psycopg
from dotenv import load_dotenv #Loads variables from .env file
import pandas as pd
from io import StringIO


#load enviroment variables from .env file
load_dotenv()

csv_file = "data/raw_stockholm.csv"

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
    Stores CSV exactly as received (no transformation).
    """

    conn = get_connection()

    with conn.cursor() as cur:

        cur.execute("CREATE SCHEMA IF NOT EXISTS raw")

        cur.execute("DROP TABLE IF EXISTS raw.stockholm_raw")

        cur.execute("""
            CREATE TABLE raw.stockholm_raw (
                line TEXT
            )
        """)

        conn.commit()

        with open(csv_file, "r", encoding="utf-8", errors="surrogateescape") as f:

            with cur.copy("COPY raw.stockholm_raw (line) FROM STDIN") as copy:

                for line in f:
                    # NO CHANGES
                    copy.write_row([line.rstrip("\n")])

    conn.commit()
    conn.close()

    '''Read Raw Data from Database'''

# Now we reconstruct the CSV into a DataFrame.
def load_raw_data():
    """
    Converts raw text into structured dataframe.
    Keeps all columns initially.
    """

    conn = get_connection()
    lines = []

    with conn.cursor() as cur:
        cur.execute("SELECT line FROM raw.stockholm_raw")

        for row in cur:
            lines.append(row[0])

    conn.close()

    # Skip metadata rows
    data_lines = lines[2:]

    rows = []

    for line in data_lines:
        parts = line.split(";")

        if len(parts) >= 3:
            rows.append(parts[:3])  # date, precipitation, temp

    df = pd.DataFrame(rows, columns=["col1", "col2", "col3"])

    return df

'''Data Transformation/Cleaning'''

"""
Now we clean the data 
convert data types and format
flag suspicious values/extreme temp and missing dates
reject impossible/invalid values 
separate valid / rejected rows
rename columns 
drop precipitation column
"""

def clean_weather_data(df):
    #Rename columns properly
    df = df.rename(columns={
        "col1": "created_at",
        "col2": "precipitation",
        "col3": "temp"
    })

    #DROP precipitation column
    df = df.drop(columns=["precipitation"])

    #Convert columns(types)
    df["created_at"] = pd.to_datetime(
        df["created_at"],
        format="mixed",
        errors="coerce"
    )

    df["temp"] = pd.to_numeric(
        df["temp"].astype(str)
        .str.replace(",", ".", regex=False),
        errors="coerce"
    ).round(1)

    # Remove duplicates FIRST (fix warning)
    df = df.drop_duplicates(subset=["created_at", "temp"]).reset_index(drop=True)

     # Flags
    df["flag_invalid_date"] = df["created_at"].isna()
    df["flag_invalid_temp"] = df["temp"].isna()
    df["flag_extreme_temp"] = (df["temp"] < -50) | (df["temp"] > 60)
    df["flag_future_date"] = df["created_at"] > pd.Timestamp.now()

    # Reject reason column
    df["reject_reason"] = ""

    df.loc[df["flag_invalid_date"], "reject_reason"] += "invalid_date; "
    df.loc[df["flag_invalid_temp"], "reject_reason"] += "invalid_temp; "
    df.loc[df["flag_extreme_temp"], "reject_reason"] += "extreme_temp; "
    df.loc[df["flag_future_date"], "reject_reason"] += "future_date; "

    df["reject_reason"] = df["reject_reason"].str.strip("; ")

     # Split
    reject_condition = df["reject_reason"] != ""

    df_rejected = df[reject_condition].copy()
    df_valid = df[~reject_condition].copy()

    return df_valid, df_rejected

'''Validation & Testing'''

    # Save rejected and valid rows

def save_validation_results(df_valid, df_rejected):

    os.makedirs("data/output", exist_ok=True)

    df_valid.to_csv("data/output/accepted_weather.csv", index=False)
    df_rejected.to_csv("data/output/rejected_weather.csv", index=False)

    '''Load Clean Data into Database'''

# Now we store clean data in a new schema.
def load_clean_data(df_clean):

    conn = get_connection()

    df_clean = df_clean[["created_at", "temp"]]

    with conn.cursor() as cur:

        cur.execute("CREATE SCHEMA IF NOT EXISTS clean")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS clean.weather (
                id SERIAL PRIMARY KEY,
                created_at DATE,
                temp FLOAT,
                UNIQUE(created_at, temp)
            )
        """)

        # Prevent duplicates on rerun
        cur.execute("TRUNCATE clean.weather")

        conn.commit()

        # Convert dataframe to CSV buffer
        buffer = StringIO()
        df_clean.to_csv(buffer, index=False, header=False)
        buffer.seek(0)

        # Bulk insert
        with cur.copy(
            "COPY clean.weather (created_at, temp) FROM STDIN WITH CSV"
        ) as copy:
            for line in buffer:
                copy.write(line)

    conn.commit()
    conn.close()



    '''Main Pipeline'''

# Finally, run everything in order.

if __name__ == "__main__":

    print("Starting ETL pipeline...")

    #loads data as it is no changes 
    ingest_raw_csv(csv_file)

    # Step 1 - Raw data already loaded by init.sql, just read it
    df_raw = load_raw_data()  # reads from raw2.chris_table

    # Step 2 - Transform
    df_valid, df_rejected = clean_weather_data(df_raw)

    # Step 3 - Save validation CSVs
    save_validation_results(df_valid, df_rejected)

    # Step 4 - Load clean data
    load_clean_data(df_valid)

    print("ETL completed successfully")


