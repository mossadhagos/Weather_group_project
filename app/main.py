"""from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello Weather"}"""

from fastapi import FastAPI, Query, HTTPException
from datetime import date
#from models import Weather




from pipeline import (
    ingest_raw_csv,
    load_raw_data,
    clean_weather_data,
    save_validation_results,
    load_clean_data,
    get_connection
)

app = FastAPI()




"""@app.get("/")
def root():
    return {"message": "Hello Weather"}"""


csv_file = "app/data/mockup_data.csv"
@app.get("/run-pipeline")
def run_pipeline():
   

    ingest_raw_csv(csv_file)

    df_raw = load_raw_data()

    df_valid, df_rejected = clean_weather_data(df_raw)

    save_validation_results(df_valid, df_rejected)

    load_clean_data(df_valid)

    return {"status": "pipeline completed"}



"""@app.get("/weather")
def get_weather():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM clean.weather_clean")
            rows = cur.fetchall()
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
    return rows"""


@app.get("/weather_by_date")
def weather_by_date(query_date: date = Query(..., description="Date to filter (YYYY-MM-DD)")):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM clean.weather_clean WHERE created_at = %s",
                (query_date,)
            )
            rows = cur.fetchall()
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
    return rows