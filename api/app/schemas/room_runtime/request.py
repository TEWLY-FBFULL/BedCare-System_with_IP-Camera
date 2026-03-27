from pydantic import BaseModel

class RoomRuntimeUpdate(BaseModel):
    camera_running: bool | None = None
    device_running: bool | None = None
    room_active: bool | None = None