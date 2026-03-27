from pydantic import BaseModel, IPvAnyAddress
from typing import Optional
from enum import Enum

class AuthTypeEnum(str, Enum):
    digest_basic = "Digest/Basic"
    basic = "Basic"

class CameraCreate(BaseModel):
    brand_id: int
    ip_address: IPvAnyAddress
    username: Optional[str]
    password: Optional[str]

class CameraUpdate(BaseModel):
    brand_id: Optional[int]
    ip_address: Optional[IPvAnyAddress]
    username: Optional[str]
    password: Optional[str]

class CameraBrandCreate(BaseModel):
    brand_name: str
    rtsp_pattern: Optional[str]
    auth_type: Optional[AuthTypeEnum]