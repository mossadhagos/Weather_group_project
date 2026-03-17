"""
import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from databases import Database
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row
import os
import asyncio
import asyncpg


import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@" \
                   f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

    # Skapa pool
    app.state.pool = ConnectionPool(database_url, row_factory=dict_row)
    print(f"ConnectionPool created: {database_url}")

    yield

    # Stäng pool vid shutdown
    app.state.pool.close()
    print("ConnectionPool closed")

app = FastAPI(lifespan=lifespan)
async def test():
    conn = await asyncpg.connect(
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT')
    )
    result = await conn.fetch("SELECT * FROM raw2.chris_table")
    print(result)
    await conn.close()

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

    # Create a connection to the database




    # Connect to database
    app.state.pool = ConnectionPool(database_url)

    yield
    app.state.pool.close()
    # Shutdown


app = FastAPI(lifespan= lifespan)

@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello Weather"}


@app.get("/all_weather_data")
async def all_weather_data():
    # Get all the dates/rows in database
    query = "SELECT * FROM raw2.chris_table;"
    result = await app.state.database.fetch_all(query=query)

    # To see if there is data in db or if something is not working
    if not result:
        return {"message": "No data in database"}

    # Create a list with dicts (for each row), returns list to user
    return {
        "all_weather_data": [
            {"created_at": row["created_at"], "temp": row["temp"]}
            for row in result
        ]
    }


@app.get("/test")
async def test():
    rows = await app.state.database.fetch_all(
        "SELECT * FROM raw2.chris_table;"
    )
    return rows

@app.get("/weather")
async def read_weather():
    rows = await app.state.database.fetch_all(
        "SELECT * FROM raw2.chris_table"
    )
    return rows

import os
import asyncio
import asyncpg

async def test():
    conn = await asyncpg.connect(
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT')
    )
    result = await conn.fetch("SELECT * FROM raw2.chris_table")
    print(result)
    await conn.close()
"""

# ./app/main.py
from fastapi import FastAPI, Depends
import psycopg

app = FastAPI()

# Dependency to get a Postgres connection per request
def get_conn():
    try:
        with psycopg.connect(
            host="postgres",           # Docker service name
            dbname="history_weather",  # your database name
            user="postgres",           # your DB user
            password="",       # your DB password
            port=5432
        ) as conn:
            yield conn
    except Exception as e:
        print("Database connection failed:", e)
        yield None

@app.get("/items")
def get_items(conn = Depends(get_conn)):
    if conn is None:
        return {"error": "Cannot connect to database"}

    with conn.cursor() as cur:
        try:
            cur.execute("SELECT * FROM public.items;")  # adjust schema.table if needed
            rows = cur.fetchall()
            # Convert tuples to dicts for JSON
            result = [dict(zip([desc[0] for desc in cur.description], row)) for row in rows] if rows else []
            return result
        except psycopg.errors.UndefinedTable:
            return {"message": "Table does not exist yet", "data": []}