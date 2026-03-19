import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from databases import Database
from datetime import date

# --- Get the information in .env-file
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@postgres:5432/{os.getenv('POSTGRES_DB')}"

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
async def all_weather_data(): #-> dict[str, list[dict[str, float | str]]]:  no type hint when trying mockdata
    # Get all the dates/rows in database
    query = "SELECT * FROM clean2.chris_table2 ORDER BY created_at"
    result = await app.state.database.fetch_all(query=query)

    # To see if there is data in db or if something is not working
    if not result:
        return {"message": "No data in database"}

    # Create a list with dicts (for each row), returns list to user
    return {
        "all_weather_data": [
            {"created_at": row["created_at"], "temperature": row["temp"]}
            for row in result
        ]
    }

