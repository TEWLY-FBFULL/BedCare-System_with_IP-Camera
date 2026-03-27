from pydantic import BaseModel
from typing import Optional

class NurseProfile(BaseModel):
    nurse_type_id: int
    nurse_type_name: str
    level_id: Optional[int]
    level_name: Optional[str]
    license_no: Optional[str]