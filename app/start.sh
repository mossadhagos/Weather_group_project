#!/bin/sh

echo "⏳ Waiting for PostgreSQL..."

# Wait until Postgres is REALLY ready
until python -c "
import psycopg
import os
try:
    psycopg.connect(
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
    )
    print('ready')
except Exception:
    exit(1)
"; do
  echo "⏳ Still waiting for database..."
  sleep 2
done

echo "✅ PostgreSQL is fully ready!"

echo "🚀 Running ETL..."
python pipeline.py

echo "🌐 Starting FastAPI..."
uvicorn main:app --host 0.0.0.0 --port 8000