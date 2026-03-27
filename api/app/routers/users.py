from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, Literal
from app.core.database import get_db
from app.core.role_guard import get_current_active_user, require_roles
from uuid import UUID
from app.models.user import User
from app.services.user_service import UserService
from app.schemas.user.base import (UserMeResponse, UserUpdateRequest, UserListResponse)
from app.schemas.user.address import AddressUpdateRequest

router = APIRouter(prefix="/users", tags=["Users"])

@router.get(
    "/me",
    summary="Get my profile",
    description="""
    ใช้สำหรับดึงข้อมูลโปรไฟล์ของผู้ใช้งานที่ทำการล็อกอินอยู่ในระบบ
    """,
    response_model=UserMeResponse
)
def get_my_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)):
    return UserService.get_user_full_profile(db, user.user_id)

@router.get(
    "/{user_id}",
    summary="Get user detail by user ID",
    description="""
    ใช้สำหรับดึงข้อมูลรายละเอียดของผู้ใช้งานตามรหัสผู้ใช้งาน (user_id)
    **Admin only**
    """,
    response_model=UserMeResponse,
    dependencies=[Depends(require_roles(["admin"]))]
)
def get_user_detail(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    return UserService.get_user_full_profile(db, user_id)

@router.get(
    "",
    summary="List all users",
    description="""
    ใช้สำหรับดึงรายการผู้ใช้งานทั้งหมดในระบบ
    **Admin only**
    **Query Parameters**
    field: กำหนดฟิลด์ที่ต้องการค้นหา (user_id, email, first_name, last_name, role, is_active) - ไม่จำเป็น ,
    keyword: คำค้นหา - ไม่จำเป็น ,
    role: กำหนดบทบาทของผู้ใช้งาน (admin, doctor, nurse, relative) - ไม่จำเป็น ,
    is_active: กำหนดสถานะการใช้งานของผู้ใช้งาน (true, false) - ไม่จำเป็น
    """,
    response_model=list[UserListResponse],
    dependencies=[Depends(require_roles(["admin"]))]
)
def list_users(
    field: Optional[
        Literal[
            "user_id",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
        ]
    ] = Query(None),
    keyword: Optional[str] = Query(None),
    role: Optional[
        Literal["admin", "doctor", "nurse", "relative"]
    ] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    return UserService.list_users(
        db=db,
        field=field,
        keyword=keyword,
        role=role,
        is_active=is_active,
    )

@router.patch(
    "/me",
    summary="Update my profile",
    description="""
    ใช้สำหรับอัปเดตข้อมูลโปรไฟล์ของผู้ใช้งานที่ทำการล็อกอินอยู่ในระบบ
    **Payload**
    first_name (ชื่อ) - ไม่จำเป็น ,
    last_name (นามสกุล) - ไม่จำเป็น ,
    phone (เบอร์โทร) - ไม่จำเป็น
    """,
)
def update_my_profile(
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return UserService.update_me(db, user, payload)

@router.patch(
    "/me/address",
    summary="Update my address",
    description="""
    ใช้สำหรับอัปเดตที่อยู่ของผู้ใช้งานที่ล็อกอินอยู่
    - จังหวัด / อำเภอ / ตำบล (ผ่าน subdistrict_id)
    - รายละเอียดบ้านเลขที่ ถนน หมู่บ้าน
    **Payload**
    house_no (บ้านเลขที่) - ไม่จำเป็น ,
    road (ถนน) - ไม่จำเป็น ,
    village (หมู่บ้าน) - ไม่จำเป็น ,
    subdistrict_id (รหัสตำบล) - จำเป็น
    """,
)
def update_my_address(
    payload: AddressUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return UserService.update_my_address(db, user, payload)