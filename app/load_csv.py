import psycopg
import csv

# Database connection parameters
DB_CONFIG = {
    "host": "postgres",          # Docker service name
    "dbname": "history_weather",
    "user": "postgres",
    "password": "",
    "port": 5432
}

# Path to your CSV inside the container (maps from ./data)
CSV_PATH = ""

# Target table name
TABLE_NAME = "items"

# Connect to Postgres
with psycopg.connect(**DB_CONFIG) as conn:
    with conn.cursor() as cur:
        # Optional: create table if not exists with TEXT columns
        with open(CSV_PATH, newline="") as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader)  # get CSV header row
            # Build CREATE TABLE statement with TEXT columns
            columns = ", ".join([f'"{h}" TEXT' for h in headers])
            cur.execute(f'CREATE TABLE IF NOT EXISTS {TABLE_NAME} ({columns});')

        # Copy CSV data into the table
        with open(CSV_PATH, "r") as f:
            cur.copy_from(f, TABLE_NAME, columns=headers, format="csv", header=True)

        print(f"CSV data loaded into table '{TABLE_NAME}' successfully!")