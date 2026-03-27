from pydantic import BaseModel
from typing import Optional

class RoomCreate(BaseModel):
    room_number: str
    facility_id: int

class RoomUpdate(BaseModel):
    room_number: Optional[str] = None

class AssignPatientRequest(BaseModel):
    patient_id: str
    note: Optional[str] = None