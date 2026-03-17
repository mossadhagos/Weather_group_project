import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from databases import Database
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

# Get the information in .env-file
load_dotenv()

# Förbereder två olika connections för att se vad som fungerar
"""
@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

    # Create a connection to the database
    app.state.database = Database(database_url)

    # Connect to database
    await app.state.database.connect()
    print("Database connected")

    yield

    # Shutdown
    await app.state.database.disconnect()
    print("Database disconnected")


app = FastAPI(lifespan= lifespan)

@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello Weather"}


@app.get("/all_weather_data")
async def all_weather_data() -> dict[str, list[dict[str, float | str]]]:
    # Get all the dates/rows in database
    query = "SELECT * FROM weather_data ORDER BY date"
    result = await app.state.database.fetch_all(query=query)

    # To see if there is data in db or if something is not working
    if not result:
        return {"message": "No data in database"}

    # Create a list with dicts (for each row), returns list to user
    return {
        "all_weather_data": [
            {"date": row["date"], "temperature": row["temperature"]}
            for row in result
        ]
    }

@app.get("/date_temp/{date}")
# When sending a request, FastAPI extracts date as a str
async def date_temperature(date: str) -> dict[str, str | float]:

    # Testing to see if date is in database
    check_query = "SELECT COUNT(*) as count FROM weather_data WHERE date = :date"
    values: dict[str, str]= {"date": date}

    count_result = await app.state.database.fetch_one(query=check_query, values=values)
    # If date not in database, return message
    if count_result["count"] == 0:
        return {"message": f"Date {date} does not exist in database"}

    # If date is in database, return date and temperature
    query = "SELECT * FROM weather_data WHERE date = :date"
    result = await app.state.database.fetch_one(query=query, values=values)

    return {"date": date, "temperature": result["temperature"]}

"""


DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('DB_HOST', 'postgres')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('POSTGRES_DB')}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.pool = ConnectionPool(DATABASE_URL)

    try:
        with app.state.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 as test")
                result = cur.fetchone()
                print(f"Database connection OK - test query: {result}")
    except Exception as e:
        print(f"Warning: Could not connect to database: {e}")

    yield

    app.state.pool.close()
    print("Database closed")


app = FastAPI(lifespan=lifespan)


#
@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello Weather"}


@app.get("/weather/{date}")
async def get_weather_by_date(date: str):
    async with app.state.pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            # Get data for specific date
            await cur.execute(
                "SELECT date, temperature FROM weather_data WHERE date = %s",
                (date,)
            )
            row = await cur.fetchone()

    # If date does not exist
    if not row:
        return {"message": f"Date {date} not found in database"}

    # Return data
    return row


@app.get("/all_weather_data")
async def all_weather_data():
    async with app.state.pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute("SELECT date, temperature FROM weather_data ORDER BY date")
            rows = await cur.fetchall()

    return rows