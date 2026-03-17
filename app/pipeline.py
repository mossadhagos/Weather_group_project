#Database Connection
#importing libraries
import os  #Allows reading environment variables like passwords

from dotenv import load_dotenv #Loads variables from .env file
from psycopg_pool import ConnectionPool
import psycopg


from datetime import datetime
from pydantic import BaseModel, ValidationError, field_validator


#load enviroment variables from .env file
load_dotenv()

csv_file = "data/mockup_data.csv"

def get_connection(): #reuasble connection function
    """
    Creates and returns a database connection.
    """
    

    conn = psycopg.connect(
        f"dbname={os.getenv('POSTGRES_DB')} "
        f"user={os.getenv('POSTGRES_USER')} "
        f"password={os.getenv('POSTGRES_PASSWORD')} "
        f"host={os.getenv('POSTGRES_HOST')}"
    )
    return conn
#Data Ingestion (Load Raw Data)
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
            CREATE SCHEMA IF NOT EXISTS raw
        """)

        # Create table for raw CSV lines
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raw.csv_raw (
                line TEXT
            )
        """)

        conn.commit()

        # Open CSV file
        with open(csv_file, "r", encoding="utf-8", errors="surrogateescape") as f:

            # COPY is the fastest way to load data(it makes bulk insert also)
            with cur.copy("COPY raw.csv_raw (line) FROM STDIN") as copy:

                for line in f:
                    copy.write_row([line.rstrip("\n")]) #inserts each line

    conn.commit()
    conn.close()
#Read Raw Data from Database
# Now we reconstruct the CSV into a DataFrame.

import pandas as pd
from io import StringIO

def load_raw_data():
    """
    Reads raw CSV lines from the database
    and converts them into a pandas dataframe.
    """

    conn = get_connection()
    lines = []

    with conn.cursor() as cur:
        cur.execute("SELECT line FROM raw.csv_raw")

        for row in cur:
            lines.append(row[0])

    conn.close()

    csv_text = "\n".join(lines) #recreates CSV 
    csv_buffer = StringIO(csv_text) #simulates file 

    df = pd.read_csv(csv_buffer, sep=';') #create dataframe

    return df
#Data Transformation/Cleaning
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
#Validation & Testing
# Save rejected and valid rows 

def save_validation_results(df_valid, df_rejected):

    df_rejected.to_csv(
        "data/output/rejected_weather.csv",
        index=False
    )

    df_valid.to_csv(
        "data/output/accepted_weather.csv",
        index=False
    )
#Load Clean Data into Database
# Now we store clean data in a new schema.

def load_clean_data(df_clean):

    conn = get_connection()

    #keep only needed columns so it does not display also the boolean from flagging 
    df_clean = df_clean[["created_at", "temp"]]

    with conn.cursor() as cur:

        # Create clean schema
        cur.execute("""
            CREATE SCHEMA IF NOT EXISTS clean
        """)

        # Create clean table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clean.weather_clean (
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
            "COPY clean.weather_clean (created_at, temp) FROM STDIN WITH CSV"
        ) as copy:

            for line in buffer:
                copy.write(line)

    conn.commit()
    conn.close()
#Query Data
#Allow the user to query temperatures for a specific date.

from datetime import datetime

def query_temperature():

    user_input = input("Enter a date (YYYY-MM-DD): ").strip()

    try:
        input_date = datetime.strptime(user_input, "%Y-%m-%d").date()
    except ValueError:
        print("Invalid date format")
        return

    conn = get_connection()

    query = """
    SELECT DISTINCT temp
    FROM clean.weather_clean
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
#Main Pipeline
# Finally, run everything in order.

if __name__ == "__main__": #It basically means:Only run the code inside this block if this file is being executed directly
                            #name is set to main because the file is in the main program ..

    csv_file = "data/mockup_data.csv"

    ingest_raw_csv(csv_file)

    df_raw = load_raw_data()

    df_valid, df_rejected = clean_weather_data(df_raw)

    save_validation_results(df_valid, df_rejected)

    load_clean_data(df_valid)
    

    query_temperature()

    