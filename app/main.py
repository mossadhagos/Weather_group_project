import os
from fastapi import FastAPI, Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from databases import Database
from datetime import date, datetime
from typing import Union
import matplotlib.pyplot as plt
import io
from fastapi.responses import StreamingResponse

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
    query = "SELECT * FROM clean.weather ORDER BY created_at"
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
    query = "SELECT * FROM clean.weather WHERE created_at = :created_at"
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
    FROM clean.weather
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


# Average temp for a give month (1 to 12) for all the years
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
    FROM clean.weather
    WHERE EXTRACT(MONTH FROM created_at) = :month AND EXTRACT (YEAR FROM created_at) < 2026
    GROUP BY year
    ORDER BY year
    """
    result = await app.state.database.fetch_all(
        query=query, values={"month": month}
    )

    if not result:
        return {"Message": f"No data for month {month}"}

# Calculate the overall average for the month for all years
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
# Average temp for all days in the chosen year
    query = """
    SELECT
    EXTRACT (YEAR from created_at) as year,
    ROUND(AVG(temp)::numeric, 1) as avg_temp
    FROM clean.weather
    WHERE EXTRACT (YEAR from created_at) = :year AND EXTRACT (YEAR FROM created_at) < 2026
    GROUP BY year
    ORDER BY year
    """
# Here we fetch single row as we filter by/for one year
    result = await app.state.database.fetch_one(
        query=query, values={"year": year}
    )

    if not result:
        return {"Message": f"No data for year {year}"}

# Return the year and its average temp
    return {
        "year": int(result["year"]),
        "avg_temp": float(result["avg_temp"])
        }


#Line chart: Temperature on the same day across years
#Parameter is a string
@app.get("/chart/same_day_all_years/{chosen_date}")
async def chart_same_day_all_years(
    chosen_date: str = Path(..., description="Date in MM-DD format")):

    parsed_date = datetime.strptime(chosen_date, "%m-%d").date() # Does not work without parsing/breaking the string
    month = parsed_date.month
    day = parsed_date.day


#Fetching all rows matching the chosen date (month and day) whatever the year
    query = """
    SELECT created_at, temp
    FROM clean.weather
    WHERE EXTRACT (MONTH FROM created_at)  = :month
    AND EXTRACT (DAY FROM created_at) = :day
    ORDER BY created_at
    """
    rows = await app.state.database.fetch_all(query=query, values={"month": month, "day": day})

    if not rows:
        return {"message": f"no data, sorry!"}

#Extracting years and temp into separate lists for plotting
    years = [r["created_at"].year for r in rows]
    temp = [float(r["temp"]) for r in rows]

#chart
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(years, temp, marker='o', linestyle='-', color='teal', linewidth=2)
    ax.set_title(f"Temperature on {parsed_date.strftime('%B %d')} Across Years")   # converts a date into a readable string
    ax.set_xlabel("Year")
    ax.set_ylabel("Temperature (°C)")
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(years, rotation=45)
    plt.tight_layout()

#Save the chart to an in-memory buffer
    buf = io.BytesIO()  # create an empty binary file in the RAM
    plt.savefig(buf, format="png", dpi=110, bbox_inches='tight') # writing the png image in the empty file
    buf.seek(0) # read the file
    plt.close(fig)

#Streaming the image directly in the endpoint
    return StreamingResponse(
     buf,   # Reads from the buffer and sends it to the browser
     media_type="image/png",
     headers={"Content-Disposition": f"inline; filename=temp{month:02d}-{day:02d}_years.png"}
    ) # Content-dips: above line says to browser how to handle the file
      # inline: display the image in the browser
      # filename: suggest a way to name the file if saved like temp_01-15_years.png
      # 02d is a format for Feb = 02


#Monthly average temperatures across years
@app.get("/chart/same_month_all_years/{chosen_month}")
async def chart_same_month_all_years(chosen_month: str = Path(..., description="Enter in MM format")):

    parsed_month = datetime.strptime(chosen_month, "%m").date()
    month = parsed_month.month

    query = """
        SELECT EXTRACT(YEAR FROM created_at) AS year,
        ROUND(AVG(temp)::numeric, 1) as avg_temp
        FROM clean.weather
        WHERE EXTRACT (MONTH from created_at)  = :month AND EXTRACT (YEAR FROM created_at) < 2026
        GROUP BY EXTRACT (YEAR from created_at)
        ORDER BY year
        """

    rows = await app.state.database.fetch_all(query=query, values={"month": month})

    if not rows:
        return {"message": f"no data, sorry!"}

    years = [int(r["year"]) for r in rows]
    avg_temp = [round(float(r["avg_temp"]), 2) for r in rows]  # changed from temp to avg_temp + rounded

    # chart
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(years, avg_temp, marker='o', linestyle='-', color='teal', linewidth=2)
    ax.set_title(f"Average Temperature on {parsed_month.strftime('%B')} Across Years")
    ax.set_xlabel("Year")
    ax.set_ylabel("Average Temperature (°C)")
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(years, rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=110, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return StreamingResponse(buf, media_type="image/png")


# Linechart: Average temperature for every month, specific year
@app.get("/chart/all_months_avg/{chosen_year}")
async def all_months_avg(
    chosen_year: str = Path(..., description="Year in YYYY format")):

    year = int(chosen_year)

    # To include all dates for a whole year (Jan 1 to Dec 31)
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # Calculate monthly average temperatures for the specified year
    query = """
    SELECT
        EXTRACT(MONTH FROM created_at) as month,
        ROUND(AVG(temp)::numeric, 2) as avg_temp,
        COUNT(*) as measurement_count
    FROM clean.weather
    WHERE created_at BETWEEN :start_date AND :end_date AND EXTRACT (YEAR FROM created_at) < 2026
    GROUP BY EXTRACT(MONTH FROM created_at)
    ORDER BY month
    """
    rows = await app.state.database.fetch_all(query=query, values={"start_date": start_date, "end_date": end_date})

    if not rows:
        return {"message": f"no data, sorry!"}

    #Extracting month and average temp into separate lists for plotting
    months = [r["month"] for r in rows]
    avg_temps = [float(r["avg_temp"]) for r in rows]

    #chart
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(months, avg_temps, marker='o', linestyle='-', color='teal', linewidth=2)
    ax.set_title(f"Average Temperature all Months, Year {chosen_year}")   # converts a date into a readable string
    ax.set_xlabel("Months")
    ax.set_ylabel("Temperature (°C)")
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(months, rotation=45)
    plt.tight_layout()

    #Save the chart to an in-memory buffer
    buf = io.BytesIO()  # create an empty binary file in the RAM
    plt.savefig(buf, format="png", dpi=110, bbox_inches='tight') # writing the png image in the empty file
    buf.seek(0) # read the file
    plt.close(fig)

    #Streaming the image directly in the endpoint
    return StreamingResponse(
     buf,   # Reads from the buffer and sends it to the browser
     media_type="image/png",
     headers={"Content-Disposition": f"inline; filename=temp_{chosen_year}_all_months.png"}
    )


@app.get("/chart/avg_temp_all_years")
async def avg_temp_all_years():


    query = """
        SELECT EXTRACT(YEAR FROM created_at) AS year,
        ROUND(AVG(temp)::numeric, 1) as avg_temp
        FROM clean.weather
        WHERE EXTRACT (YEAR FROM created_at) < 2026
        GROUP BY EXTRACT (YEAR from created_at)
        ORDER BY year
        """

    rows = await app.state.database.fetch_all(query=query)

    if not rows:
        return {"message": f"no data, sorry!"}

    years = [int(r["year"]) for r in rows]
    avg_temp = [round(float(r["avg_temp"]), 2) for r in rows]  # changed from temp to avg_temp + rounded

    # chart
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(years, avg_temp, marker='o', linestyle='-', color='teal', linewidth=2)
    ax.set_title(f"Average Temperature for all Years in Database")
    ax.set_xlabel("Year")
    ax.set_ylabel("Average Temperature (°C)")
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(years, rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=110, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return StreamingResponse(buf, media_type="image/png")