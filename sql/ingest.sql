-- Create schema
CREATE SCHEMA IF NOT EXISTS raw;

-- Drop table if exists
DROP TABLE IF EXISTS raw.stockholm_raw;

-- Create table
CREATE TABLE raw.stockholm_raw (
    line TEXT
);

-- Load file (must match Docker-mounted path)
COPY raw.stockholm_raw(line)
FROM '/data/raw_stockholm.csv'
WITH (FORMAT text);


--- for cleaned data 
-- Create schema
CREATE SCHEMA IF NOT EXISTS clean;

-- Create table
CREATE TABLE IF NOT EXISTS clean.weather (
    id SERIAL PRIMARY KEY,
    created_at DATE,
    temp FLOAT,
    UNIQUE(created_at, temp)
);
