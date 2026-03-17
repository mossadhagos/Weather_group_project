from pydantic import BaseModel
from datetime import date

class Weather_Validation(BaseModel):
    temp: float
    created_at: date
    is_flagged: bool