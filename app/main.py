import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from databases import Database
from datetime import date
from typing import Union

# Get the information from .env-file
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@postgres:5432/{os.getenv('POSTGRES_DB')}"

    # Create a connection to the database
    app.state.database = Database(database_url)


    # Connect to database
    await app.state.database.connect()
    print("Database connected")

    yield # When app is up and running (takes and handles requests)

    # Shutdown
    await app.state.database.disconnect()
    print("Database disconnected")


app = FastAPI(lifespan= lifespan)

# Message in root-folder
@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Hello Weather"}


@app.get("/all_weather_data")
async def all_weather_data()-> Union[dict[str, str], dict[str, list[dict[str, date | float]]]]:
    # Get all the rows in the table (in database)
    query = "SELECT * FROM clean2.chris_table2 ORDER BY created_at"
    # await -> pauses, lets other requests run, go when databas has responded (possible by async)
    result = await app.state.database.fetch_all(query=query)

    # To see if there is data in db (used when testing)
    if not result:
        return {"message": "No data in database"}

    # Create a list with dicts (for each row), returns dict with list to user
    return {
        "all_weather_data": [
            {"created_at": row["created_at"], "temperature": row["temp"]}
            for row in result
        ]
    }


@app.get("/date_temp/{created_at}")
async def date_temperature(created_at: date) -> dict[str, Union[date, float]]:
    # Get the row with requested date
    query = "SELECT * FROM clean2.chris_table2 WHERE created_at = :created_at"
    result = await app.state.database.fetch_one(query=query, values={"created_at": created_at})

    # If date does not exist in db, sends message
    if not result:
        return {"message": f"There is no data for this date: {created_at}"}

    # If date exists, returns both date and temperature
    return {
        "created_at": result["created_at"],
        "temperature": result["temp"]
    }