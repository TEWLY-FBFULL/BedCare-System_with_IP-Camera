from pydantic import BaseModel
from typing import Optional, List

class DeviceCreate(BaseModel):
    device_name: Optional[str]

class DeviceUpdate(BaseModel):
    device_name: Optional[str]
    is_active: Optional[bool]

class SensorCreate(BaseModel):
    sensor_types: List[str]

class DeviceLoginRequest(BaseModel):
    device_token: str
