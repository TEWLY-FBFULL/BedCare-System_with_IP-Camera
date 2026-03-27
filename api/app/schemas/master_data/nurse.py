from pydantic import BaseModel

class NurseTypeResponse(BaseModel):
    nurse_type_id: int
    nurse_type_name: str
    class Config:
        from_attributes = True