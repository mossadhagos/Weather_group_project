import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from databases import Database

# Get the information in .env-file
load_dotenv()

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

#
@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello Weather"}


@app.get("/all_weather_data")
async def all_weather_data() -> dict[str, list[dict[str, float]]]:
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
