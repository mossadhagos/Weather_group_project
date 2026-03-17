from pydantic_schema import Weather_Validation
import csv
from pydantic import ValidationError
import psycopg
from dotenv import load_dotenv
import os

load_dotenv()

valid = []
not_valid = []

with open(r'df_accepted.csv', encoding='utf-8') as file:
    read_file = csv.DictReader(file)
    for id, row in enumerate(read_file, start=1):
        print(id, row)
        try:
            check = Weather_Validation(**row)
            valid.append(check)
        except ValidationError as e:
            print(f"Error: {e}, at {id}")

conn = psycopg.connect(
    f"dbname={os.getenv('POSTGRES_DB')} user={os.getenv('POSTGRES_USER')} password={os.getenv('POSTGRES_PASSWORD')} host={os.getenv('POSTGRES_HOST')}"
)

with conn:
    with conn.cursor() as cur:
        for user in valid:
            cur.execute(
                """
                INSERT INTO weather_data (temp, created_at, is_flagged)
                VALUES (%s, %s, %s)
                """,
                (user.temp, user.created_at, user.is_flagged)
            )