from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.role_guard import get_current_active_user
from app.services.room_service import RoomService
from app.schemas.room.request import RoomCreate, RoomUpdate, AssignPatientRequest
from app.schemas.room.response import RoomDetailOut
from app.models.user import User

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.get(
    "/{room_id}",
    summary="Get room detail",
    description="""
    ดึงรายละเอียดห้องพักตามรหัสห้องพัก (room_id) ในสถานที่ดูแลที่ผู้ใช้งานสังกัดอยู่
    **สิทธิ์การเข้าถึง:**
    admin เห็นทั้งหมด ,
    owner / manager เห็นเฉพาะห้องพักที่อยู่ในสถานที่ดูแลที่ตนเองสังกัดอยู่ ,
    ผู้ใช้งานทั่วไปเห็นเฉพาะห้องพักที่อยู่ในสถานที่ดูแลที่ตนเองสังกัดอยู่เเละต้องเกี่ยวข้องกับผู้ป่วยที่พักในห้องนั้น
    """,
    response_model=RoomDetailOut)
def get_room(room_id:int,
    db:Session=Depends(get_db),
    user:User=Depends(get_current_active_user)
):
    return RoomService.get(db, user=user, room_id=room_id)


@router.post(
    "",
    summary="Create new room",
    description="""
    สร้างห้องพักใหม่ในสถานที่ดูแลที่ผู้ใช้งานสังกัดอยู่
    **สิทธิ์การเข้าถึง:**
    เฉพาะ owner , manager เท่านั้นที่จะสามารถสร้างห้องพักในสถานที่ดูแลที่ตนเองสังกัดอยู่ได้
    **Payload**
    room_number: หมายเลขห้องพัก ,
    facility_id: รหัสสถานที่ดูแล (ต้องเป็นสถานที่ดูแลที่ผู้ใช้งานสังกัดอยู่)
    """,
)
def create_room( 
    payload:RoomCreate, 
    db:Session=Depends(get_db), 
    user:User=Depends(get_current_active_user)
):
    return RoomService.create(db, user=user, payload=payload)


@router.post(
    "/{room_id}/assign",
    summary="Assign patient to room",
    description="""
    กำหนดให้ผู้ป่วยเข้าพักในห้องพักที่ระบุ
    **สิทธิ์การเข้าถึง:**
    เฉพาะ owner , manager เท่านั้นที่จะสามารถ assign ผู้ป่วยให้เข้าพักในห้องพักที่ตนเองสังกัดอยู่ได้
    **Payload**
    patient_id: รหัสผู้ป่วยที่ต้องการ assign จำเป็น ,
    note: หมายเหตุเพิ่มเติมสำหรับการ assign ไม่จำเป็น
    """,
)
def assign_patient(
    room_id:int,
    payload:AssignPatientRequest,
    db:Session=Depends(get_db),
    user:User=Depends(get_current_active_user)
):
    return RoomService.assign_patient(db, user=user, room_id=room_id, payload=payload)


@router.patch(
    "/{room_id}",
    summary="Update room",
    description="""
    แก้ไขข้อมูลห้องพักในสถานที่ดูแลที่ผู้ใช้งานสังกัดอยู่
    **สิทธิ์การเข้าถึง:**
    เฉพาะ owner , manager เท่านั้นที่จะสามารถเเก้ไขห้องพักได้
    **Payload**
    room_number: หมายเลขห้องพัก (ไม่จำเป็น) ,
    """,
)
def update_room(
    room_id:int, 
    payload:RoomUpdate, 
    db:Session=Depends(get_db), 
    user:User=Depends(get_current_active_user)
):
    return RoomService.update(db, user=user, room_id=room_id, payload=payload)


@router.delete(
    "/{room_id}",
    summary="Delete room and all data in room",
    description="""
    ลบห้องพักและข้อมูลที่เกี่ยวข้องทั้งหมด (room_id) ในสถานที่ดูแลที่ผู้ใช้งานสังกัดอยู่
    **สิทธิ์การเข้าถึง:**
    owner / admin เท่านั้นที่ลบอุปกรณ์ในห้องพักที่ตัวเองสังกัดอยู่ได้
    """
)
def delete_room(room_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_active_user)):
    return RoomService.delete(db,user=user,room_id=room_id)