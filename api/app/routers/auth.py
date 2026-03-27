from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.role_guard import get_current_active_user
from app.models.user import User
from app.services.auth_service import AuthService
from app.schemas.auth.doctor import DoctorRegister
from app.schemas.auth.nurse import NurseRegister
from app.schemas.auth.relative import RelativeRegister
from app.schemas.auth.base import LoginRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.auth.token import TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])
auth_service = AuthService()
    
@router.post(
    "/register/doctor",
    summary="Register a doctor account",
    description="""
    ใช้สำหรับลงทะเบียนผู้ใช้งานประเภท **แพทย์ (Doctor)** ในระบบ SleepCare
    **Payload**
    first_name (ชื่อ) ,
    last_name (นามสกุล) ,
    email (อีเมล) ,
    phone (เบอร์โทร) ,
    password (รหัสผ่าน) ,
    specialty_id (รหัสสาขาแพทย์) ,
    level_id (รหัสระดับวิชาชีพ) ,
    license_no (เลขใบประกอบวิชาชีพ)
    """
)
def register_doctor(payload: DoctorRegister, db: Session = Depends(get_db)):
    try:
        user = auth_service.register_doctor(db, payload)
        return {"user_id": user.user_id, "role": "doctor"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/register/nurse",
    summary="Register a nurse account",
    description="""
    ใช้สำหรับลงทะเบียนผู้ใช้งานประเภท **พยาบาล (Nurse)** ในระบบ SleepCare
    **Payload**
    first_name (ชื่อ) ,
    last_name (นามสกุล) ,
    email (อีเมล) ,
    phone (เบอร์โทร) ,
    password (รหัสผ่าน) ,
    specialty_id (รหัสประเภทพยาบาล) ,
    level_id (รหัสระดับวิชาชีพ) ,
    license_no (เลขใบประกอบวิชาชีพ)
    """
)
def register_nurse(payload: NurseRegister, db: Session = Depends(get_db)):
    try:
        user = auth_service.register_nurse(db, payload)
        return {"user_id": user.user_id, "role": "nurse"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/register/relative",
    summary="Register a relative account",
    description="""
    ใช้สำหรับลงทะเบียนผู้ใช้งานประเภท **ญาติ (Relative)** ในระบบ SleepCare
    **Payload**
    first_name (ชื่อ) ,
    last_name (นามสกุล) ,
    email (อีเมล) ,
    phone (เบอร์โทร) ,
    password (รหัสผ่าน) ,
    """
)
def register_relative(payload: RelativeRegister, db: Session = Depends(get_db)):
    try:
        user = auth_service.register_relative(db, payload)
        return {"user_id": user.user_id, "role": "relative"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post(
    "/login", 
    response_model=TokenResponse,
    summary="User login",
    description="""
    ใช้สำหรับเข้าสู่ระบบ SleepCare
    **Payload**
    email (อีเมล) ,
    password (รหัสผ่าน)
    """
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        token = auth_service.login(db, payload.email, payload.password)
        return {"access_token": token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    
@router.get(
    "/verify-email",
    summary="Verify email",
    description="""
    ใช้สำหรับยืนยันอีเมลของผู้ใช้งานผ่านลิงก์ที่ส่งไปยังอีเมล
    **Query Parameters** 
    token (โทเค็นยืนยันอีเมล)
    """
)
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        return auth_service.verify_email(db, token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post(
    "/forgot-password",
    summary="Forgot password",
    description="""
    ใช้สำหรับส่งลิงก์ reset password ไปที่อีเมลผู้ใช้งาน
    **Payload**
    email (อีเมล)
    """
)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    try:
        return auth_service.forgot_password(db, payload.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post(
    "/reset-password",
    summary="Reset password",
    description="""
    ใช้สำหรับรีเซ็ตรหัสผ่านด้วย token ที่ได้จากอีเมล
    **Payload**
    token (โทเค็นรีเซ็ตรหัสผ่าน) ,
    new_password (รหัสผ่านใหม่)
    """
)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        return auth_service.reset_password(db, payload.token, payload.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post(
    "/logout",
    summary="Logout",
    description="ใช้สำหรับออกจากระบบ โดยจะทำการยกเลิกโทเค็นที่ใช้งานอยู่"
)
def logout(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)):
    return auth_service.logout(db, user)