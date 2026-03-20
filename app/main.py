import os
from fastapi import FastAPI, Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from databases import Database
from datetime import date
from typing import Union


# Get the information in .env-file
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
async def date_temperature(created_at: date = Path(..., description="Enter date in YYYY-MM-DD format")) -> dict[str, Union[date, float]]:
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


# Same day for all the years ---
@app.get("/same_day_all_years/{created_at}")
async def same_day_all_years(created_at: date = Path(...,description="Enter a date in YYYY-MM-DD format")):
# Query rows matching the same month and day for all the years ---
    query = """
    SELECT created_at, temp
    FROM clean2.chris_table2
    WHERE EXTRACT(MONTH FROM created_at) = :month
    AND EXTRACT(DAY FROM created_at) = :day
    ORDER BY created_at
    """
# Extract month and day from the input date ---
    result = await app.state.database.fetch_all(
        query=query, values={"month": created_at.month, "day": created_at.day}
    )

    if not result:
        return {"message": "No data, sorry!"}

# Return the day and one entry per year
    return {
        "created_at": created_at.strftime("%B %d"),
        "view": [
            {"year": row["created_at"].year, "temp": row["temp"]}
            for row in result
        ]
    }


# Average temp for a give month (1 to 12) for all the years ---
@app.get("/monthly_average_all_years/{month}")
async def monthly_average_all_years(month: int = Path(..., description="Enter a number for the month from 1 to 12")):
# Validation of the months'number
    if month < 1 or month > 12:
        return {"Message": "Month numbers go from 1 to 12"}

# Average temp per year for the chosen month | ""::numeric, 1" converts the result into a numeric as Postgres only accepts ROUND for numeric type
    query = """
    SELECT 
        EXTRACT(YEAR FROM created_at) as year,
        ROUND(AVG(temp)::numeric, 1) as avg_temp 
    FROM clean2.chris_table2
    WHERE EXTRACT(MONTH FROM created_at) = :month
    GROUP BY year
    ORDER BY year
    """
    result = await app.state.database.fetch_all(
        query=query, values={"month": month}
    )

    if not result:
        return {"Message": f"No data for month {month}"} 

# Calculate the overall average for the month for all years ---
    overall = round(sum(r["avg_temp"] for r in result) / len(result), 1)

# Return the overall averages and split them by year ---
    return {
        "month": month,
        "overall_average": overall,
        "by_year": [
            {"year": int(row["year"]), "avg_temp": float(row["avg_temp"])}
            for row in result
        ]
    }


@app.get("/yearly_average_temperature/{year}")
async def yearly_average_temperature(year: int = Path(..., description="Enter year as YYYY")):
# Average temp for all days in the chosen year ---
    query = """
    SELECT
    EXTRACT (YEAR from created_at) as year,
    ROUND(AVG(temp)::numeric, 1) as avg_temp
    FROM clean2.chris_table2
    WHERE EXTRACT (YEAR from created_at) = :year
    GROUP BY year
    ORDER BY year
    """
# Here we fetch single row as we filter by/for one year ---
    result = await app.state.database.fetch_one(
        query=query, values={"year": year}
    )

    if not result:
        return {"Message": f"No data for year {year}"} 

# Return the year and its average temp ---
    return {
        "year": int(result["year"]),
        "avg_temp": float(result["avg_temp"])
        }
   