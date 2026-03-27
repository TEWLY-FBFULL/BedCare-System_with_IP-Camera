from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.facility_service import FacilityService
from app.core.database import get_db 
from app.core.role_guard import get_current_active_user
from app.models.user import User
from app.schemas.facility.request import (
    FacilityCreate,
    FacilityUpdate,
    FacilityUpdateAddress,
    FacilityShareRequest
)
from app.schemas.facility.response import FacilityOut,  FacilityAllRoomOut
from typing import List

router = APIRouter(prefix="/facilities", tags=["Facilities"])

@router.get(
    "", 
    summary="List facilities for current user",
    description="""
    ดึงรายการสถานที่ดูแลทั้งหมดที่ผู้ใช้งานมีสิทธิ์เข้าถึงหรือกำลังสังกัดอยู่ตอนนี้
    **สิทธิ์การเข้าถึง:** 
    admin เห็นทั้งหมด , 
    ผู้ใช้งานทั่วไปเห็นเฉพาะสถานที่ดูแลที่ตนเองสังกัดอยู่
    """,
    response_model=List[FacilityOut])
def list_facilities(db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    return FacilityService.list_for_user(db, user)


@router.get(
    "/{facility_id}", 
    summary="Get facility detail",
    description="""
    ดึงรายละเอียดสถานที่ดูแลตามรหัสสถานที่ดูแล (facility_id)
    **สิทธิ์การเข้าถึง:** 
    admin เห็นทั้งหมด , 
    ผู้ใช้งานทั่วไปเห็นเฉพาะสถานที่ดูแลที่ตนเองสังกัดอยู่
    """,
    response_model=FacilityOut)
def get_facility(facility_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)
):
    return FacilityService.get(db, user=user, facility_id=facility_id)


@router.get(
    "/{facility_id}/rooms", 
    summary="Get all rooms in a facility",
    description="""
    ดึงห้องเเละผู้ป่วยในห้องทั้งหมดในสถานที่ดูแลตามรหัสสถานที่ดูแล (facility_id)
    **สิทธิ์การเข้าถึง:** 
    ทุกคนในสถานที่ดูแลสามารถเห็นห้องพักและผู้ป่วยในห้องพักได้
    """,
    response_model=FacilityAllRoomOut)
def get_facility_rooms(facility_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)
):
    return FacilityService.get_rooms(db, user=user, facility_id=facility_id)


@router.post(
    "",
    summary="Create facility",
    description="""
    สร้างสถานที่ดูแลใหม่
    **สิทธิ์การเข้าถึง:** 
    ทุกบทบาทสามารถสร้างสถานที่ดูแลได้ ยกเว้น admin
    **Payload**
    facility_name(ชื่อสถานที่ดูแล) จำเป็น ,
    facility_type(ประเภทสถานที่ดูแล) home/hospital/other ไม่จำเป็น
    **กรณีใช้ที่อยู่เดียวกันกลับผู้ใช้**
    address_id(รหัสที่อยู่) จำเป็น
    **กรณีใช้ที่อยู่ใหม่**
    house_no(บ้านเลขที่) ไม่จำเป็น ,
    road(ถนน) ไม่จำเป็น ,
    village(หมู่บ้าน) ไม่จำเป็น ,
    subdistrict_id(รหัสตำบล) จำเป็น (มาจาก masterdata api จังหวัด อำเภอ ตำบล)
    """
)
def create_facility(payload: FacilityCreate,db: Session = Depends(get_db),user: User = Depends(get_current_active_user)
):
    return FacilityService.create(db, user_id=user.user_id, payload=payload)


@router.patch(
    "/{facility_id}", 
    summary="Update facility",
    description="""
    อัปเดตข้อมูลสถานที่ดูแล
    **สิทธิ์การเข้าถึง:** 
    เฉพาะ owner , manager เท่านั้น
    **Payload** 
    facility_name(ชื่อสถานที่ดูแล) ไม่จำเป็น ,
    facility_type(ประเภทสถานที่ดูแล) home/hospital/other ไม่จำเป็น ,
    address_id(รหัสที่อยู่) ไม่จำเป็น
    """,
)
def update_facility(facility_id: int,payload: FacilityUpdate,db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return FacilityService.update(db,user_id=user.user_id,facility_id=facility_id,payload=payload)


@router.delete(
    "/{facility_id}",
    summary="Delete facility",
    description="""
    ลบสถานที่ดูแล
    **สิทธิ์การเข้าถึง:** 
    เฉพาะ admin เเละ owner เท่านั้น
    """,
)
def delete_facility(facility_id: int,db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return FacilityService.delete(db, user=user, facility_id=facility_id)


@router.patch(
    "/{facility_id}/address",
    summary="Update facility address",
    description="""
    อัปเดตที่อยู่ของสถานที่ดูแล
    **สิทธิ์การเข้าถึง:** 
    เฉพาะ owner , manager เท่านั้น
    **Payload** 
    house_no(บ้านเลขที่) ไม่จำเป็น ,
    road(ถนน) ไม่จำเป็น ,
    village(หมู่บ้าน) ไม่จำเป็น ,
    subdistrict_id(รหัสตำบล) ไม่จำเป็น
    """
)
def update_facility_address(
    facility_id: int,
    payload: FacilityUpdateAddress,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return FacilityService.update_address(db, user=current_user,
            facility_id=facility_id,payload=payload)


@router.post(
    "/{facility_id}/share",
    summary="Share facility access to another user",
    description="""
    ใช้สำหรับแชร์สิทธิ์การเข้าถึงสถานที่ดูแลให้กับผู้ใช้งานอื่นผ่านทางอีเมล
    **สิทธิ์การเข้าถึง:** 
    เฉพาะ owner , manager เท่านั้น
    **Payload**
    email(อีเมลผู้รับ) จำเป็น ,
    role_in_facility(บทบาทในสถานที่ดูแล) doctor/nurse/caregiver/manager จำเป็น
    """,
)
def share_facility(facility_id: int,payload: FacilityShareRequest,db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return FacilityService.share_facility(db, user=current_user,
            facility_id=facility_id, payload=payload)


@router.post(
    "/share/accept",
    summary="Accept facility share invitation",
    description="""
    **สิทธิ์การเข้าถึง:**
    ทุกบทบาทสามารถรับคำเชิญได้ ยกเว้น admin
    ใช้สำหรับยอมรับคำเชิญแชร์สถานที่ดูแล ต้อง login ก่อนใช้งาน
    **Query Parameters**
    token(รหัสคำเชิญ) จำเป็น
    """,
)
def accept_share(token: str, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return FacilityService.accept_facility_share(db, user=current_user, token=token)