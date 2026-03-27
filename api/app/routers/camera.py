from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.role_guard import get_current_active_user, require_roles
from app.services.camera_service import CameraService
from app.schemas.camera.request import CameraCreate, CameraUpdate
from app.schemas.camera.response import CameraOut, CameraBrandOut
from app.models.user import User

router = APIRouter(prefix="/rooms", tags=["Rooms Camera"])

@router.get(
    "/meta/camera-brands", 
    summary="get camera brands",
    description="""
    ดึงข้อมูลเเบรนด์กล้องทั้งหมดที่รองรับในระบบ
    """,
    response_model=list[CameraBrandOut]
)
def get_camera_brand(db:Session=Depends(get_db), user:User=Depends(get_current_active_user)):
    return CameraService.get_all(db,user=user)


@router.get(
    "/{room_id}/camera", 
    summary="get camera in room",
    description="""
    ดึงข้อมูลกล้องของห้องพักตามรหัสห้องพัก (room_id) ในสถานที่ดูแลที่ผู้ใช้งานสังกัดอยู่
    **สิทธิ์การเข้าถึง:**
    admin เห็นทั้งหมด ,
    ทุกคนในสถานที่ดูเเลเห็นกล้องในห้องพักที่ตัวเองสังกัดอยู่ได้
    """,
    response_model=CameraOut
)
def get_camera(room_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_active_user)):
    return CameraService.get(db,user=user,room_id=room_id)


@router.post(
    "/{room_id}/camera", 
    summary="create camera in room",
    description="""
    สร้างกล้องในห้องพักตามรหัสห้องพัก (room_id) ในสถานที่ดูแลที่ผู้ใช้งานสังกัดอยู่
    **สิทธิ์การเข้าถึง:**
    owner / manager สร้างกล้องในห้องพักที่ตัวเองสังกัดอยู่ได้
    **Payload**
    brand_id: รหัสเเบรนด์กล้องที่มีในระบบ
    ip_address: ที่อยู่ IP ของกล้อง
    username: ชื่อผู้ใช้สำหรับกล้อง (ถ้ามี)
    password: รหัสผ่านสำหรับกล้อง (ถ้ามี)
    """
)
def create_camera(room_id:int, payload:CameraCreate, db:Session=Depends(get_db), user:User=Depends(get_current_active_user)):
    return CameraService.create(db,user=user,room_id=room_id,payload=payload)


@router.post(
    "/brand-camera", 
    summary="create camera brand",
    description="""
    สร้างเเบรนด์กล้องใหม่ในระบบ
    **สิทธิ์การเข้าถึง:**
    admin เท่านั้นที่สามารถสร้างเเบรนด์กล้องใหม่ได้
    **Payload**
    brand_name: ชื่อเเบรนด์กล้องที่มีในระบบ
    rtsp_pattern: รูปแบบ RTSP URL สำหรับกล้องของเเบรนด์นี้
    auth_type: ประเภทการยืนยันตัวตน (ถ้ามี)
    """,
    dependencies=[Depends(require_roles(["admin"]))]
)
def create_camera_brand(payload:CameraCreate, db:Session=Depends(get_db), 
    user:User=Depends(get_current_active_user)):
    return CameraService.create_camera_brand(db,user=user,payload=payload)


@router.patch(
    "/{room_id}/camera", 
    summary="update camera in room",
    description="""
    อัปเดตข้อมูลกล้องในห้องพักตามรหัสห้องพัก (room_id) ในสถานที่ดูแลที่ผู้ใช้งานสังกัดอยู่
    **สิทธิ์การเข้าถึง:**
    owner / manager อัปเดตกล้องในห้องพักที่ตัวเองสังกัดอยู่ได้
    **Payload**
    brand_id: รหัสเเบรนด์กล้องที่มีในระบบ (ถ้ามี)
    ip_address: ที่อยู่ IP ของกล้อง (ถ้ามี)
    username: ชื่อผู้ใช้สำหรับกล้อง (ถ้ามี)
    password: รหัสผ่านสำหรับกล้อง (ถ้ามี)
    """,
)
def update_camera(room_id:int, payload:CameraUpdate, db:Session=Depends(get_db), user:User=Depends(get_current_active_user)):
    return CameraService.update(db,user=user,room_id=room_id,payload=payload)


@router.delete(
    "/{room_id}/camera",
    summary="delete camera in room",
    description="""
    ลบกล้องในห้องพักตามรหัสห้องพัก (room_id) ในสถานที่ดูแลที่ผู้ใช้งานสังกัดอยู่
    **สิทธิ์การเข้าถึง:**
    owner / admin เท่านั้นที่ลบกล้องในห้องพักที่ตัวเองสังกัดอยู่ได้
    """,
)
def delete_camera(room_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_active_user)):
    return CameraService.delete(db,user=user,room_id=room_id)