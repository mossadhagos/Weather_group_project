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
    """
    Cleans the dataframe and separates
    valid and rejected rows.
    """

    # Convert columns
    df['created_at'] = pd.to_datetime(df['created_at'], format= "mixed", errors='coerce')
    df['temp'] = pd.to_numeric(df['temp'].astype(str)
        .str.replace('"', '', regex=False)
        .str.replace(",", ".", regex=False),errors='coerce').round(1)

    # Flag invalid rows
    df["flag_invalid_date"] = df["created_at"].isna()
    df["flag_invalid_temp"] = df["temp"].isna()
    df["flag_extreme_temp"] = df["temp"]>= 100 
    df["flag_invalid_timestamp"] = df["created_at"] > pd.Timestamp.now()
    #try out > 3 digits 

    reject_condition = (
        df["flag_invalid_date"] |
        df["flag_invalid_temp"] |
        df["flag_extreme_temp"] |
        df["flag_invalid_timestamp"]

    )

    #Drops duplicates based on dates and temperature columns 
    

    df= df.drop_duplicates(subset=["created_at" , "temp"]) #.reset_index(drop=True)


    # Separate datasets
    df_rejected= df[reject_condition].copy()
    df_valid= df[~reject_condition].copy()

    
    # try to send directly to the database 
    #df_valid = df_valid.drop_duplicates(subset=["created_at" , "temp"]).reset_index(drop=True)

    return df_valid, df_rejected


'''Validation & Testing'''

# Save rejected and valid rows 

def save_validation_results(df_valid, df_rejected):

    import os
    os.makedirs("data/output", exist_ok=True)  # ← added this line

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

    #keep only needed columns so it does not display also the boolean from flagging 
    df_clean = df_clean[["created_at", "temp"]]

    with conn.cursor() as cur:

        # Create clean schema
        cur.execute("""
            CREATE SCHEMA IF NOT EXISTS clean2
        """)

        # Create clean table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clean2.chris_table2 (
                id SERIAL PRIMARY KEY,
                created_at DATE ,
                temp FLOAT
            )
        """)

        conn.commit()

        # Convert dataframe to CSV buffer
        buffer = StringIO()
        df_clean.to_csv(buffer, index=False, header=False)
        buffer.seek(0)

        # Bulk insert
        with cur.copy(
            "COPY clean2.chris_table2 (created_at, temp) FROM STDIN WITH CSV"
        ) as copy:

            for line in buffer:
                copy.write(line)

    conn.commit()
    conn.close()

'''# Query Data'''

#Allow the user to query temperatures for a specific date.

#from datetime import datetime

def query_temperature():

    # Instead of: user_input = input("Enter a date (YYYY-MM-DD): ")
    user_input = os.getenv("QUERY_DATE", "1990-01-01")  
    
    try:
        input_date = datetime.strptime(user_input, "%Y-%m-%d").date()
    except ValueError:
        print("Invalid date format")
        return

    conn = get_connection()

    query = """
    SELECT DISTINCT temp
    FROM clean2.chris_table2
    WHERE DATE(created_at) = %s
    """

    with conn.cursor() as cur:
        cur.execute(query, (input_date,))
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]

    conn.close()

    df = pd.DataFrame(rows, columns=colnames)

    if df.empty:
         print(f"No data found for {input_date}")
    else:
         print(f"Data for {input_date}:")
         print(df)

'''Main Pipeline'''

# Finally, run everything in order.

if __name__ == "__main__":

    # Step 1 - Raw data already loaded by init.sql, just read it
    df_raw = load_raw_data()  # reads from raw2.chris_table

    # Step 2 - Transform
    df_valid, df_rejected = clean_weather_data(df_raw)

    # Step 3 - Save validation CSVs
    save_validation_results(df_valid, df_rejected)

    # Step 4 - Load clean data
    load_clean_data(df_valid)

    # Step 5 - Query for demo date
    query_temperature()