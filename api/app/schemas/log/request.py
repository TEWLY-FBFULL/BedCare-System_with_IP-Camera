from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LogQueryParams(BaseModel):
    days: int = Field(..., example=7)
    patient_id: Optional[str] = None