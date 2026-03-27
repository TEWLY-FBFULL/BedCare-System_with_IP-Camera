from pydantic import BaseModel, EmailStr
from datetime import date
from app.schemas.patient.base import PatientBase
from app.schemas.patient.base import GenderEnum
from typing import Optional, Literal

class PatientCreateRequest(PatientBase):
    weight: Optional[float] = None
    height: Optional[float] = None
    notes: Optional[str] = None
    facility_id: int

class PatientShareRequest(BaseModel):
    email: EmailStr
    role: Literal["relative", "nurse", "doctor"]

class PatientUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[GenderEnum] = None
    birth_date: Optional[date] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    notes: Optional[str] = None