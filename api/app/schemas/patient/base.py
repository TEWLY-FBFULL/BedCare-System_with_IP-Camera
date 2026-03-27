from pydantic import BaseModel
from typing import Optional
from datetime import date
from enum import Enum

class GenderEnum(str, Enum):
    male = "ชาย"
    female = "หญิง"
    other = "อื่นๆ"
    unspecified = "ไม่ระบุ"

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    gender: Optional[GenderEnum] = None
    birth_date: Optional[date] = None

