# Glossary For Workflow/Project
---

## Tools

- Docker – A platform that packages applications and their dependencies into lightweight, portable containers for consistent deployment.

- FastAPI – A modern, fast (high-performance) web framework for building APIs with Python, based on standard Python type hints.

---
## Python & Environment

 - import – Loads a module or library into your Python script so you can use its functions and classes.

 - os – A built-in Python module for interacting with the operating system, like reading environment variables or file paths.

 - psycopg – A PostgreSQL adapter for Python, used to connect and run SQL queries in PostgreSQL databases.

 - dotenv / load\_dotenv() – Loads environment variables from a .env file into Python’s environment (os.environ), keeping sensitive info like passwords out of code.

 - os.getenv() – Reads an environment variable, returning its value or None if it doesn’t exist.

 - \_\_name\_\_ == "\_\_main\_\_" – Ensures a block of code runs only when the script is executed directly, not when imported as a module.


---

## Database Concepts


 - PostgreSQL – An open-source relational database.

 - Connection (psycopg.connect()) – Establishes a link between Python and the database.

 - Cursor (conn.cursor()) – Object used to execute SQL commands and fetch data.

 - Schema – A namespace in the database used to organize tables. Example: raw or clean.

 - Table – Structured storage for data with rows and columns.

 - CREATE SCHEMA IF NOT EXISTS – SQL command to create a schema if it doesn’t already exist.

 - COPY – PostgreSQL command for bulk inserting data from a file or buffer, faster than individual INSERT statements.

 - Commit (conn.commit()) – Saves changes made in the database.

 - Close (conn.close()) – Closes the connection to free resources.
---

## Data Handling

 - CSV (Comma-Separated Values) – A text file format for tabular data, where each line is a row, and values are separated by a delimiter (like ;).

 - Raw Data – Original data as received, before any cleaning or transformation.

 - DataFrame (pandas.DataFrame) – A 2D tabular data structure in Python (from pandas), similar to a spreadsheet or SQL table.

 - StringIO – A Python object that lets you treat strings like a file, useful for simulating reading/writing CSVs in memory.

---

## Data Transformation & Cleaning

 - pd.to\_datetime() – Converts a column to datetime objects.

 - pd.to\_numeric() – Converts a column to numeric type (int/float).