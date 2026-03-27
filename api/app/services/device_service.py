from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from fastapi import HTTPException
from datetime import datetime, timezone
import os
from app.models.device import Device
from app.models.sensor import Sensor
from app.models.room import Room
from app.models.user import User
from app.models.enum import SensorTypeEnumClass
from app.models.room_runtime_status import RoomRuntimeStatus
from app.services.config_cache import ConfigCache
from app.services.email_service import EmailService
from app.schemas.device.request import SensorCreate
from app.services.permission import (
    Action, 
    get_role_name,
    can_access_room,
)
from uuid import uuid4

class DeviceService:

    @staticmethod
    def get(db, *, user: User, room_id: int):
        if not can_access_room(db, user_id=user.user_id, room_id=room_id, action=Action.READ) \
        and get_role_name(db, user) != "admin":
            raise HTTPException(403, "ไม่มีสิทธิ์")
        device = (
            db.query(Device)
            .options(joinedload(Device.sensors))
            .filter(
                Device.room_id == room_id,
                Device.is_active == True
            )
            .first()
        )
        if not device:
            raise HTTPException(404, "ไม่พบอุปกรณ์ในห้องนี้หรืออุปกรณ์ถูกปิดใช้งานอยู่")
        return device
    
    @staticmethod
    def get_sensor_types_(user:User):
        return { "sensor_types": [sensor.value for sensor in SensorTypeEnumClass]}

    @staticmethod
    def create(db, *, user: User, room_id: int, payload):
        if not can_access_room(db, user_id=user.user_id, room_id=room_id, action=Action.CREATE):
            raise HTTPException(403, "ไม่มีสิทธิ์")
        if not user.email:
            raise HTTPException(400, "ผู้ใช้ต้องมีอีเมลเพื่อรับข้อมูลอุปกรณ์")
        existing = db.query(Device).filter(
            Device.room_id == room_id
        ).first()
        if existing: raise HTTPException(400, "ห้องนี้มีอุปกรณ์แล้ว")
        # room + facility
        room = (
            db.query(Room)
            .options(joinedload(Room.facility))
            .filter(Room.room_id == room_id)
            .first()
        )
        if not room: raise HTTPException(404, "ไม่พบห้อง")
        if not room.facility: raise HTTPException(404, "ไม่พบสถานที่ดูแล")
        if not room.facility.facility_type:
            raise HTTPException(400, "ประเภทของสถานที่ดูแลไม่ถูกต้อง")
        device = Device(
            room_id=room_id,
            device_name=payload.device_name,
            device_token=uuid4().hex
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        EmailService.send_new_device_data_to_email(
            email=user.email,
            payload={
                "facility_name": room.facility.facility_name,
                "room_name": room.room_number,
                "device_id": device.device_id,
                "device_token": device.device_token,
                "URL": os.getenv("DEVTEST_URL").rstrip("/") + "/rooms/devices/login"
            }
        )
        return { "message": "สร้างอุปกรณ์สำเร็จ หากอีเมลถูกต้องทางระบบจะส่งข้อมูลไป" }
    
    @staticmethod
    def create_sensors(db: Session, *, user: User, room_id: int, payload: SensorCreate):
        if not can_access_room(db, user_id=user.user_id, room_id=room_id, action=Action.CREATE):
            raise HTTPException(403, "ไม่มีสิทธิ์")
        device = db.query(Device).filter(
            Device.room_id == room_id
        ).first()
        if not device: raise HTTPException(404, "ไม่พบอุปกรณ์ในห้อง")
        if not payload.sensor_types:
            raise HTTPException(400, "กรุณาระบุประเภทเซ็นเซอร์อย่างน้อย 1 รายการ")

        new_sensors = []
        for s_type in set(payload.sensor_types):
            sensor = Sensor(
                device_id=device.device_id,
                sensor_type=s_type
            )
            new_sensors.append(sensor)
        try:
            db.add_all(new_sensors)
            db.commit()
            return { 
                "message": f"สร้างเซ็นเซอร์สำเร็จทั้งหมด {len(new_sensors)} รายการ",
                "added_types": [s.sensor_type for s in new_sensors]
            }
        except Exception as e:
            db.rollback()
            print(f"Error creating sensors: {e}")
            raise HTTPException(500, "เกิดข้อผิดพลาดในการบันทึกข้อมูลเซ็นเซอร์")
    
    @staticmethod
    def update(db:Session, *, user:User, room_id:int, payload):
        if not can_access_room(db, user_id=user.user_id, room_id=room_id, action=Action.UPDATE):
            raise HTTPException(403,"ไม่มีสิทธิ์")
        device = db.query(Device).filter(
            Device.room_id == room_id
        ).first()
        if not device:
            raise HTTPException(404,"ไม่พบอุปกรณ์หรืออุปกรณ์ถูกปิดใช้งานอยู่")
        for k, v in payload.dict(exclude_unset=True).items():
            setattr(device,k,v)
        db.commit()
        db.refresh(device)
        return { "message": "อัปเดตอุปกรณ์สำเร็จ" }

    @staticmethod
    def delete(db:Session, *, user:User, room_id:int):
        if not can_access_room(db, user_id=user.user_id, room_id=room_id, action=Action.DELETE) \
        and get_role_name(db,user) != "admin":
            raise HTTPException(403,"ไม่มีสิทธิ์")
        device = db.query(Device).filter(
            Device.room_id == room_id
        ).first()
        if not device:
            raise HTTPException(404,"ไม่พบอุปกรณ์")
        db.delete(device)
        db.commit()
        return {"message":"ลบอุปกรณ์และเซ็นเซอร์สำเร็จ"}
    
    @staticmethod
    def login(db: Session, *, device_token: str):
        device = db.query(Device).filter(
            Device.device_token == device_token
        ).first()
        if not device:
            raise HTTPException(401, "device token ไม่ถูกต้อง")
        if not device.is_active:
            raise HTTPException(403, "device ถูกปิดใช้งาน")
        device.last_seen_at = datetime.now(timezone.utc)
        runtime = db.query(RoomRuntimeStatus).filter(
            RoomRuntimeStatus.room_id == device.room_id
        ).first()
        if not runtime:
            raise HTTPException(500, "room runtime status ไม่พบ")
        if not runtime.room_active:
            raise HTTPException(403, "ห้องถูกปิด runtime")
        runtime.device_running = True
        runtime.last_env_log = datetime.now(timezone.utc)
        runtime.updated_at = datetime.now(timezone.utc)
        db.commit()
        room = (
            db.query(Room)
            .options(joinedload(Room.facility))
            .filter(Room.room_id == device.room_id)
            .first()
        )
        if not room:
            raise HTTPException(404, "ไม่พบห้อง")
        if not room.facility:
            raise HTTPException(400, "ไม่พบสถานที่ดูแล")
        topic_prefix = room.facility.facility_type
        mqtt_topic = f"{topic_prefix}/{device.room_id}/environment"
        env_interval = ConfigCache.get("env_log_interval_sec")
        if not env_interval:
            raise HTTPException(500, "env_log_interval_sec not configured")
        env_interval = int(env_interval)
        return {
            "device_id": device.device_id,
            "mqtt_host": os.getenv("MQTT_HOST_EXTERNAL"),
            "mqtt_port": int(os.getenv("MQTT_PORT_EXTERNAL")),
            "mqtt_topic": mqtt_topic,
            "env_log_interval_sec": env_interval,
            "mqtt_auth": {
                "username": os.getenv("MQTT_USERNAME"),
                "password": os.getenv("MQTT_PASSWORD")
            }
        }