from pydantic import BaseModel, Field

class SystemConfigOut(BaseModel):
    config_key: str
    config_value: str
    description: str | None
    class Config:
        orm_mode = True

class SystemConfigUpdate(BaseModel):
    config_value: str = Field(..., example="300")