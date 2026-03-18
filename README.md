# Weather_group_project

# TEST CSV Ingestion into PostgreSQL via Docker

*Suggestion - Test for documentation purpose only

## Test

We tested the ingestion of a local mockup CSV file "mockup_data.csv" into the PostgreSQL database "History_weather" running in Docker, using a SQL script. The test setup uses two schemas: `raw2` for dirty/unclean data and `clean2` for future cleaned data.

```
The data was in a local folder called "data_c/" and the script in "sql/". Both were listed in ".gitignore" and must never be committed or pushed to main
```

## Setup

### 1. docker-compose.yml (volumes section)


We added the two local mounts to the postgres service:

```yaml
volumes:
  - postgres_data:/var/lib/postgresql   # shared team config — do not remove
  - ./data_c:/data                      # local only, gitignored
  - ./sql:/docker-entrypoint-initdb.d   # local only, gitignored
```
!: PostgreSQL automatically runs any .sql file placed in /docker-entrypoint-initdb.d on first startup.

---

### 2. init.sql

<img src = "0.sql_test2_schema_table.png" width=500>

```sql
-- Raw and clean schemas ---
CREATE SCHEMA IF NOT EXISTS raw2;
CREATE SCHEMA IF NOT EXISTS clean2;

-- Raw table, 2 columns as TEXT ---
CREATE TABLE IF NOT EXISTS raw2.chris_table (
    created_at TEXT,
    temp       TEXT
);

-- Clean table, samme as above --- 
CREATE TABLE IF NOT EXISTS clean2.chris_table2 (
    created_at DATE,
    temp       FLOAT
);

-- Bulk ingest CSV, delimiter and header --- 
COPY raw2.chris_table (created_at, temp)
FROM '/data/mockup_data.csv'
DELIMITER ';'
CSV HEADER;
```

---

### Start the container (fresh start)

<img src="1.docker_ps.png" width=500>


```bash
docker-compose down -v   # wiped the existing volume to start testing
docker-compose up        # started fresh — init.sql runs automatically
```

### Verify the container is running

```bash
docker ps
```

You should see `history_weather` (postgres), `fastapi`, and `kafka` containers up.

---

## Inspecting the Database

<img src="2.docker_into_dbs.png" witdh=500>

```bash
# Connect to the database
docker exec -it history_weather psql -U postgres -d History_weather
```

Once inside `psql`:

<img src="3.docker_check_schemas.png" width=500>

```sql
\dn                            -- list schemas (raw2, clean2, public)

<img src="4.docker_check_table.png" width=500>

\dt raw2.*                     -- list tables in raw2


<img src ="5.docker_see_ingested_data.png" width=500>

SELECT * FROM raw2.chris_table; -- view ingested data (20 rows)

\q                             -- quit
```

---

## Expected Results

| Check | Result |
|---|---|
| `\dn` | `raw2`, `clean2`, `public` visible |
| `\dt raw2.*` | `chris_table` visible |
| `SELECT *` | 20 rows of dirty data ingested as-is |

The raw data intentionally contains dirty values (mixed date formats, nulls, invalid numbers) for later cleaning into `clean2`.

---

## Dropping Schemas and Tables

To remove only your schemas without affecting the rest of the database:

```sql
DROP SCHEMA IF EXISTS raw2 CASCADE;    -- drops schema + all its tables
DROP SCHEMA IF EXISTS clean2 CASCADE;
```

---


