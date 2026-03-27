from pydantic import BaseModel

class DoctorSpecialtyResponse(BaseModel):
    specialty_id: int
    specialty_name: str
    class Config:
        from_attributes = True