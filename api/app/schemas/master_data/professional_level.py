from pydantic import BaseModel

class ProfessionalLevelResponse(BaseModel):
    level_id: int
    level_name: str
    class Config:
        from_attributes = True