#!/bin/bash

DB_HOST="postgres"
CONTAINER_NAME="history_weather"
DB_USER="${POSTGRES_USER}"
DB_NAME="${POSTGRES_DB}"
export PGPASSWORD="${POSTGRES_PASSWORD}"

echo "--- 1. Running init.sql (create schemas, tables & load data) ---"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f /init-scripts/init.sql

echo "--- 2. Running test query on raw2.chris_table ---"
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT * FROM raw2.chris_table;"

echo "--- Done! ---"