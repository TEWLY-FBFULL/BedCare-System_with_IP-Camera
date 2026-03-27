from typing_extensions import runtime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
from app.models.room_runtime_status import RoomRuntimeStatus
from app.models.user import User

from app.services.permission import (
    can_access_room,
    Action
)

class RoomRuntimeService:

    @staticmethod
    def get(db: Session, *, user: User, room_id: int):
        if not can_access_room(
            db,
            user_id=user.user_id,
            room_id=room_id,
            action=Action.READ
        ):
            raise HTTPException(403, "ไม่มีสิทธิ์เข้าถึง")
        runtime = db.query(RoomRuntimeStatus).filter(
            RoomRuntimeStatus.room_id == room_id
        ).first()
        if not runtime:
            raise HTTPException(404, "ไม่พบ runtime ของห้อง")
        return runtime

    @staticmethod
    def update(db: Session, *, user: User, room_id: int, payload):
        if not can_access_room(
            db,
            user_id=user.user_id,
            room_id=room_id,
            action=Action.UPDATE
        ):
            raise HTTPException(403, "ไม่มีสิทธิ์แก้ไข runtime")
        runtime = db.query(RoomRuntimeStatus).filter(
            RoomRuntimeStatus.room_id == room_id
        ).first()
        if not runtime:
            raise HTTPException(404, "ไม่พบ runtime ของห้อง")
        data = payload.dict(exclude_unset=True)
        if "device_running" in data and data["device_running"] is True:
            raise HTTPException(400,"ไม่สามารถเปิด device_running ผ่านช่องทางนี้ได้ ต้องให้ device login ใหม่")
        # apply fields
        for k, v in data.items():
            setattr(runtime, k, v)
        if "camera_running" in data and data["camera_running"] is True:
            runtime.last_ai_run = datetime.now(timezone.utc)
        if runtime.room_active is False:
            runtime.last_env_log = None
            runtime.last_ai_run = None
            runtime.camera_running = False
            runtime.device_running = False
        runtime.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(runtime)
        return runtime