from pydantic import BaseModel
from datetime import date


class Weather(BaseModel):
    id: int
    created_at: date
    temp: float
