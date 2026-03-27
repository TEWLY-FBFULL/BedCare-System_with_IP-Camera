from pydantic import BaseModel
from typing import Optional

class DoctorProfile(BaseModel):
    specialty_id: int
    specialty_name: str
    level_id: Optional[int]
    level_name: Optional[str]
    license_no: Optional[str]