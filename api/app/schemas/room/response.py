from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date, datetime
from app.schemas.patient.base import GenderEnum

class RoomOut(BaseModel):
    room_id: int
    room_number: str
    facility_id: int
    class Config:
        orm_mode = True

class RoomPatientDetail(BaseModel):
    patient_id: UUID
    first_name: str
    last_name: str
    gender: Optional[GenderEnum]
    birth_date: Optional[date]
    weight: Optional[float]
    height: Optional[float]
    notes: Optional[str]
    address_id: Optional[int]
    assigned_at: datetime
    class Config:
        orm_mode = True

class RoomDetailOut(BaseModel):
    room_id: int
    room_number: str
    facility_id: int
    is_occupied: bool
    patient: Optional[RoomPatientDetail] = None
    class Config:
        orm_mode = True
