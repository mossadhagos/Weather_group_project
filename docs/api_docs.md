# Information about fastapi/endpoints/main.py:
---

- A connection to the database in docker is created with FastAPI for the possibility of sending requests through endpoints and get response with the data that matches the request. 

---

- The connection is built with an async context manager, which creates the connection to the database. When Docker is built, the app starts. The yield keyword keeps the app open for requests, and the app shuts down when the Docker environment is closed down.

---

- The use of async when creating the endpoints makes it possible for a request to pause until the database responds. Other requests can run in the meantime and this makes things run smoother and faster.




