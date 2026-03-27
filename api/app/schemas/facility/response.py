from pydantic import BaseModel
from app.schemas.facility.base import FacilityBase
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.schemas.facility.base import FacilityTypeEnum
from app.schemas.user.address import AddressInfo

class FacilityOut(FacilityBase):
    facility_id: int
    address: Optional[AddressInfo] = None
    class Config:
        orm_mode = True

class RoomPatientInfo(BaseModel):
    patient_id: UUID
    first_name: str
    last_name: str
    assigned_at: datetime

class RoomOut(BaseModel):
    room_id: int
    room_number: str
    is_occupied: bool
    patient: Optional[RoomPatientInfo] = None

class FacilityAllRoomOut(BaseModel):
    facility_id: int
    facility_name: str
    facility_type: Optional[FacilityTypeEnum] = None
    address: Optional[AddressInfo] = None
    rooms: list[RoomOut]