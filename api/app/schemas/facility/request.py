from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
from app.schemas.facility.base import FacilityTypeEnum

class FacilityShareRequest(BaseModel):
    email: EmailStr
    role_in_facility: Literal["doctor","nurse","caregiver","manager"]

class FacilityCreateAddress(BaseModel):
    house_no: Optional[str] = None
    road: Optional[str] = None
    village: Optional[str] = None
    subdistrict_id: int

class FacilityCreate(BaseModel):
    facility_name: str
    facility_type: Optional[FacilityTypeEnum] = None
    address_id: Optional[int] = None
    address: Optional[FacilityCreateAddress] = None

class FacilityUpdate(BaseModel):
    facility_name: Optional[str] = None
    facility_type: Optional[FacilityTypeEnum] = None
    address_id: Optional[int] = None

class FacilityUpdateAddress(BaseModel):
    house_no: Optional[str] = None
    road: Optional[str] = None
    village: Optional[str] = None
    subdistrict_id: Optional[int] = None