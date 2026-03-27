from pydantic import BaseModel
from datetime import datetime

class RoomRuntimeOut(BaseModel):
    room_id: int
    camera_running: bool
    device_running: bool
    room_active: bool
    last_ai_run: datetime | None
    last_env_log: datetime | None
    updated_at: datetime | None
    class Config:
        orm_mode = True