from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SensorOut(BaseModel):
    sensor_id: int
    sensor_type: str
    class Config:
        orm_mode = True

class DeviceOut(BaseModel):
    device_id: int
    device_name: str
    is_active: bool
    last_seen_at: Optional[datetime]
    sensors: List[SensorOut] = Field(default_factory=list)
    class Config:
        orm_mode = True

class DeviceCreateOut(BaseModel):
    message: str

class MQTTAuth(BaseModel):
    username: str
    password: str

class DeviceLoginResponse(BaseModel):
    device_id: int
    mqtt_host: str
    mqtt_port: int
    mqtt_topic: str
    env_log_interval_sec: int
    mqtt_auth: MQTTAuth

