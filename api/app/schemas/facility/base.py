from pydantic import BaseModel
from typing import Optional
from enum import Enum

class FacilityTypeEnum(str, Enum):
    home="home"
    hospital="hospital" 
    other="other"

class FacilityBase(BaseModel):
    facility_name: str
    facility_type: Optional[FacilityTypeEnum] = None
