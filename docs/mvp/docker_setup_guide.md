# Docker Setup and PostgreSQL Data Ingestion Walkthrough

*Note: the naming convention may have changed, for example from "raw2" ---> "raw" and from "clean2" ---> "clean".


This guide explains how to:
- start the Docker container, 
- connect to the PostgreSQL database,
- run the initialization script, 
- verify that the data has been ingested.

## The steps

1. **Start Docker deskstop**

2. **Create and run the container** (including the PostgreSQL database) with: <br>
docker compose up

<img src="images/2.step.png" width=500>
<br>
<br>
3. **Open an interactive terminal** (with -it) inside the container "history_weather": <br>
docker exec -it history_weather bash

<img src="images/3.step.png" width=500>
<br>
<br>
4. **List all the files/directories** inside the container:<br>
ls

<img src="images/4.step.png" width=500>
<br>
<br>
5. **Go into the relevant folder**, here docker-entrypoint-initdb.d/ by doing:<br> 
cd docker-entrypoint-initdb.d/

<img src="images/5.step.png" width=500>
<br>
<br>
6. *Check that the ingest.sql file* (initialization) is there:<br> 
ls

<img src="images/6.step.png" width=500>
<br>
<br>
7. **Connect to the PostgreSQL database using the psql CLI** ("-U postgres" connects as postgres user and "-d history_weather" connects to the dbs "history_weather"):<br>
psql -U postgres -d history_weather

<img src="images/7.step.png" width=500>
<br>
<br> 
=> You can see 
- the schemas by doing: \dn
- the dbs by doing: \l

<img src="images/schemas.png" width=200> 
<img src="images/dbs.png" width=500>
<br>
<br>
8. **Connect to the database** "history_weather":<br>
\c history_weather

<img src="images/8.step.png" width=500>
<br>
<br>
9. **Run the SQL ingest script to create the schemas, tables and load** the data:<br>
\i '/docker-entrypoint-initdb.d/ingest.sql'

<img src="images/9.step.png" width=500>
<br>
<br>
10. **Query the table** to check that the data was successfully ingested:<br>
SELECT * FROM raw2.chris_table LIMIT 20;