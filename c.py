import os

print("DB Host:", os.getenv("POSTGRES_HOST"))
print("DB Name:", os.getenv("POSTGRES_DB"))
print("DB User:", os.getenv("POSTGRES_USER"))
print("DB Port:", os.getenv("POSTGRES_PORT"))