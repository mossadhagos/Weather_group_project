# load_db.py
import os
import time
from dotenv import load_dotenv
import psycopg

# 1️⃣ Load environment variables
# Adjust path if your .env is in a different folder
load_dotenv()

DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5432))

print(DB_NAME)

# 2️⃣ Retry logic for Postgres startup
MAX_RETRIES = 10
SLEEP_SECONDS = 2

for attempt in range(1, MAX_RETRIES + 1):
    try:
        conn = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        print(f"✅ Connected to database '{DB_NAME}' on host '{DB_HOST}'")
        break
    except psycopg.OperationalError as e:
        print(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}")
        if attempt == MAX_RETRIES:
            print("❌ Could not connect to database. Exiting.")
            exit(1)
        time.sleep(SLEEP_SECONDS)

# 3️⃣ Example query to test connection
try:
    with conn.cursor() as cur:
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        print("Test query result:", result)
finally:
    conn.close()