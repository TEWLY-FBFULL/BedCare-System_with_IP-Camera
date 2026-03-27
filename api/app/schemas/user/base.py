from pydantic import BaseModel, EmailStr, Field, validator
from uuid import UUID
from datetime import datetime
from typing import Optional
from .address import AddressInfo
from .doctor import DoctorProfile
from .nurse import NurseProfile

class UserMeResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str]
    role: str
    email_verified: bool
    is_active: bool
    created_at: datetime
    address: Optional[AddressInfo] = None
    doctor_profile: Optional[DoctorProfile] = None
    nurse_profile: Optional[NurseProfile] = None

class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = Field(None, min_length=9, max_length=10) 

    @validator("phone")
    def validate_phone(cls, v: str):
        if not v.isdigit():
            raise ValueError("เบอร์โทรต้องเป็นตัวเลขเท่านั้น")
        return v

class UserListResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True
