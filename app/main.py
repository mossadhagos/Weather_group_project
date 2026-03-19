import os
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from databases import Database

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

# Dubble queries created problems when running the code

"""
@app.get("/date_temp/{created_at}")
#When sending a request, FastAPI extracts date as a str
async def date_temperature(created_at: str): # -> dict[str, str | float]:  no type hint when trying mockdata

    # Testing to see if date is in database
    check_query = "SELECT COUNT() as count FROM raw2.chris_table WHERE created_at = :created_at"
    values: dict[str, str]= {"created_at": created_at}

    count_result = await app.state.database.fetch_one(query=check_query, values=values)
    # If date not in database, return message
    if count_result["count"] == 0:
        return {"message": f"Date {created_at} does not exist in database"}

    # If date is in database, return date and temperature
    query = "SELECT FROM raw2.chris_table WHERE created_at = :created_at"
    result = await app.state.database.fetch_one(query=query, values=values)

    return {
        "created_at": str(result["created_at"]) if result["created_at"] is not None else None, 
        "temperature": str(result["temp"]) if result["temp"] is not None else None
    }
"""
# --- Changes need to make it work ---
@app.get("/date_temp/{created_at}")
async def date_temperature(created_at: str):
    query = "SELECT * FROM clean2.chris_table2 WHERE created_at = :created_at"
    result = await app.state.database.fetch_one(query=query, values={"created_at": created_at})

    if not result:
        return {"message": f"Date {created_at} does not exist"}

    return {
        "created_at": result["created_at"],
        "temperature": result["temp"]
    }