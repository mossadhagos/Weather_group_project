# Docker Setup and PostgreSQL Data Ingestion Walkthrough

This guide explains how to:
- start the Docker container, 
- connect to the PostgreSQL database,
- run the initialization script, 
- verify that the data has been ingested.

## The steps

1. **Start Docker deskstop**

2. **Create and run the container** (including the PostgreSQL database) with: <br>
docker compose up

<img src="2.docker_compose_up.png" width=500>

3. **Open an interactive terminal** (with -it) inside the container "history_weather": <br>
docker exec -it history_weather bash

<img src="3.step.png" width=500>

4. **List all the files/directories** inside the container:<br>
ls

<img src="4.step.png" width=500>

5. **Go into the relevant folder**, here docker-entrypoint-initdb.d/ by doing:<br> 
cd docker-entrypoint-initdb.d/

<img src="5.step" width=500>

6. *Check that the init.sql file* (initialization) is there:<br> 
ls

<img src="6.step.png" width=500>

7. **Connect to the PostgreSQL database using the psql CLI** ("-U postgres" connects as postgres user and "-d history_weather" connects to the dbs "history_weather"):<br>
psql -U postgres -d history_weather

<img src="7.step.png" width=500>
<br>
<br>
=> You can see 
- the schemas by doing: \dn
- the dbs by doing: \l

<img src="schemas.png" width=500>
<img src="dbs" width=500>

8. **Connect to the database** "history_weather":<br>
\c history_weather

<img src="8.step.png" width=500>

9. **Run the SQL init script to create the schemas, tables and load** the data:<br>
\i '/docker-entrypoint-initdb.d/init.sql'

<img src="9.step.png" width=500>

10. **Query the table** to check that the data was successfully ingested:<br>
SELECT * FROM raw2.chris_table LIMIT 20;

