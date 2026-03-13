from fastapi import FastAPI
from dotenv import load_dotenv
import os
from databases import Database
import asyncpg

# Get the information in .env-file
load_dotenv()
# Create the connection to database
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
database = Database(DATABASE_URL)

app = FastAPI()

#
@app.get("/")
def root():
    return {"message": "Hello Weather"}

# Start the connection to the database when container starts
@app.on_event("startup")
async def startup():
    await database.connect()

# Close the connection to the database when docker is shut down
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/date_temperature/{date}")
async def date_temperature(date: str):
    # Testing to see if date is in database
    check_query = "SELECT COUNT(*) as count FROM weather_data WHERE date = :date"
    values= {"date": date}

    count_result = await database.fetch_one(query=check_query, values=values)
    # If date not in database, return message
    if count_result["count"] == 0:
        return {"message": f"Date {date} does not exist in database"}

    # If date is in database, return date and temperature
    query = "SELECT * FROM weather_data WHERE date = :date"
    result = await database.fetch_one(query=query, values=values)

    return {"date": date, "temperature": result["temperature"]}


