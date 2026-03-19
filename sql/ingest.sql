--- Raw and clean test schemas ---
CREATE SCHEMA IF NOT EXISTS raw2;
CREATE SCHEMA IF NOT EXISTS clean2;

--- Raw table with 2 columns with TEXT type to take in all errors ---
CREATE TABLE IF NOT EXISTS raw2.chris_table (
    created_at TEXT,
    temp TEXT
);

--- Clean table, same principles ---
CREATE TABLE IF NOT EXISTS clean2.chris_table2 (
    created_at DATE,
    temp      FLOAT
);

--- Bulk ingest into table with path, delimeter and header ---
COPY raw2.chris_table (created_at, temp)
FROM '/data/mockup_data.csv'
DELIMITER ';'
CSV HEADER;
