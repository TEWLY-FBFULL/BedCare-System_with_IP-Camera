from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.models.camera import Camera
from app.models.camera_brand import CameraBrand
from app.models.user import User
from app.models.room_runtime_status import RoomRuntimeStatus
from app.utils.password import encrypt_password
from app.services.permission import (
    Action, 
    get_role_name,
    can_access_room,
)
from app.services.sleep_service import SleepService
from app.ai.pipeline import run_sleep_ai
from app.ai.aggregation import aggregation_buffers
from datetime import datetime, timezone

class CameraService:

    @staticmethod
    def get_all(db: Session, *, user: User):
        brands = db.query(CameraBrand).all()
        if not brands: raise HTTPException(404, "ไม่พบยี่ห้อกล้อง")
        return brands

    @staticmethod
    def get(db:Session, *, user:User, room_id:int):
        if not can_access_room(db,user_id=user.user_id, room_id=room_id, action=Action.READ) \
        and get_role_name(db,user) != "admin":
            raise HTTPException(403,"ไม่มีสิทธิ์หรือไม่พบห้อง")
        camera = db.query(Camera).filter(
            Camera.room_id == room_id,
            Camera.is_active == True
        ).first()
        if not camera: raise HTTPException(404,"ไม่พบกล้องในห้องนี้หรือกล้องถูกปิดใช้งานอยู่")
        return camera

    @staticmethod
    def create(db: Session, *, user, room_id: int, payload):
        if not can_access_room(db, user_id=user.user_id, room_id=room_id, action=Action.CREATE):
            raise HTTPException(403, "ไม่มีสิทธิ์หรือไม่พบห้อง")
        existing = db.query(Camera).filter(
            Camera.room_id == room_id
        ).first()
        if existing:
            raise HTTPException(400, "ห้องนี้มีกล้องแล้ว")
        brand = db.query(CameraBrand).filter(
            CameraBrand.brand_id == payload.brand_id
        ).first()
        if not brand: raise HTTPException(404, "ไม่พบยี่ห้อกล้อง")
        try:
            runtime = db.query(RoomRuntimeStatus).filter(
                RoomRuntimeStatus.room_id == room_id
            ).first()
            if not runtime:
                raise HTTPException(500, "room runtime status ไม่พบ")
            if not runtime.room_active:
                raise HTTPException(403, "ห้องถูกปิด runtime")
            runtime.camera_running = True
            runtime.last_ai_run = datetime.now(timezone.utc)
            runtime.updated_at = datetime.now(timezone.utc)
            camera = Camera(
                room_id=room_id,
                brand_id=payload.brand_id,
                ip_address=str(payload.ip_address), 
                username=payload.username,
                password=encrypt_password(payload.password)
            )
            db.add(camera)
            db.add(runtime)
            db.commit()
            db.refresh(camera)
            return {"message": "สร้างกล้องสำเร็จ"}
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(400, "ข้อมูลไม่ถูกต้องหรือรูปแบบ IP ผิด")
    
    @staticmethod
    def update(db:Session, *, user:User, room_id:int, payload):
        if not can_access_room(db, user_id=user.user_id, room_id=room_id, action=Action.UPDATE):
            raise HTTPException(403,"ไม่มีสิทธิ์หรือไม่พบห้อง")
        camera = db.query(Camera).filter(
            Camera.room_id == room_id
        ).first()
        if not camera: raise HTTPException(404,"ไม่พบกล้อง")
        if payload.brand_id:
            brand = db.query(CameraBrand).filter(
                CameraBrand.brand_id == payload.brand_id
            ).first()
            if not brand: raise HTTPException(404, "ไม่พบยี่ห้อกล้อง")
        try:
            for k,v in payload.dict(exclude_unset=True).items():
                if k == "ip_address" and v is not None:
                    v = str(v)
                if k == "password":
                    v = encrypt_password(v)
                setattr(camera,k,v)
            db.commit()
            db.refresh(camera)
            return {"message":"อัปเดตกล้องสำเร็จ"}
        except SQLAlchemyError:
            db.rollback()
            raise HTTPException(400,"ข้อมูลไม่ถูกต้องหรือรูปแบบ IP ผิด")
    
    @staticmethod
    def delete(db:Session, *, user:User, room_id:int):
        if not can_access_room(db, user_id=user.user_id, room_id=room_id, action=Action.DELETE) \
        and get_role_name(db,user) != "admin":
            raise HTTPException(403,"ไม่มีสิทธิ์หรือไม่พบห้อง")
        camera = db.query(Camera).filter(
            Camera.room_id == room_id
        ).first()
        if not camera: raise HTTPException(404,"ไม่พบกล้อง")
        db.delete(camera)
        db.commit()
        return {"message":"ลบกล้องสำเร็จ"}
    
    @staticmethod
    def create_camera_brand(db: Session, *, user:User, payload):
        if get_role_name(db,user) != "admin":
            raise HTTPException(403,"ไม่มีสิทธิ์")
        brand = CameraBrand(
            brand_name=payload.brand_name,
            rtsp_pattern=payload.rtsp_pattern,
            auth_type=payload.auth_type
        )
        db.add(brand)
        db.commit()
        db.refresh(brand)
        return brand
    
    @staticmethod
    def process_frame(room_id, frame):
        print(f"DEBUG: Processing frame for room {room_id}...")
        result = run_sleep_ai(frame)
        if not result:
            return
        buffer = aggregation_buffers.get(room_id)
        if not buffer:
            return
        buffer.add(result)
        if buffer.ready():
            aggregated = buffer.aggregate()
            if aggregated:
                SleepService.save(room_id, aggregated)
