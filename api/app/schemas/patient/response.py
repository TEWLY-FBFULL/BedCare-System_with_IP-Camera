from pydantic import BaseModel
from typing import Optional
from datetime import  datetime, date
from uuid import UUID
from app.schemas.patient.base import GenderEnum

class PatientDetailResponse(BaseModel):
    patient_id: UUID
    first_name: str
    last_name: str
    gender: Optional[GenderEnum]
    birth_date: Optional[date]
    weight: Optional[float]
    height: Optional[float]
    notes: Optional[str]
    address_id: Optional[int]
    created_at: datetime
    class Config:
        orm_mode = True

class PatientListResponse(BaseModel):
    patient_id: UUID
    first_name: str
    last_name: str
    created_at: datetime
    class Config:
        orm_mode = True

class PatientUserResponse(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    relation_type: str  # caregiver | relative | doctor
    class Config:
        orm_mode = True