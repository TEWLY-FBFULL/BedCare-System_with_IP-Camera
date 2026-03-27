from pydantic import BaseModel
from typing import Optional
from app.schemas.camera.request import AuthTypeEnum

class CameraOut(BaseModel):
    camera_id: int
    brand_id: int
    ip_address: str
    class Config:
        orm_mode = True

class CameraBrandOut(BaseModel):
    brand_id: int
    brand_name: str
    rtsp_pattern: Optional[str]
    auth_type: Optional[AuthTypeEnum]
    class Config:
        orm_mode = True