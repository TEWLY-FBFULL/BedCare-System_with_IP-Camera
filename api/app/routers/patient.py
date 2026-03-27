from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.core.role_guard import get_current_active_user, require_roles
from app.services.patient_service import PatientService
from app.schemas.patient.request import PatientCreateRequest, PatientUpdateRequest, PatientShareRequest
from app.schemas.patient.response import PatientDetailResponse, PatientListResponse, PatientUserResponse
from app.models.user import User

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get(
    "",
    summary="List patients",
    description="""
    ดึงรายการผู้ป่วยทั้งหมดที่ผู้ใช้งานมีสิทธิ์เข้าถึง
    **สิทธิ์การเข้าถึง:**
    admin: เห็นทั้งหมด ,
    relative: เห็นเฉพาะญาติ ,
    nurse: เห็นเฉพาะผู้ป่วยที่ดูแล ,
    doctor: เห็นเฉพาะผู้ป่วยที่ดูแล
    """,
    response_model=list[PatientListResponse]
)
def list_patients(db: Session = Depends(get_db),user: User = Depends(get_current_active_user)
): return PatientService.list_patients(db, user)


@router.get(
    "/{patient_id}",
    summary="Get patient detail",
    description="""
    ดึงรายละเอียดผู้ป่วยจากตาราง patients
    (ไม่รวม address, rooms, logs)
    **สิทธิ์การเข้าถึง:**
    admin: เห็นทั้งหมด ,
    relative: เห็นเฉพาะญาติ ,
    nurse: เห็นเฉพาะผู้ป่วยที่ดูแล ,
    doctor: เห็นเฉพาะผู้ป่วยที่ดูแล
    """,
    response_model=PatientDetailResponse
)
def get_patient_detail(patient_id: UUID,db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
): return PatientService.get_patient_detail(db, user, patient_id)


@router.get(
    "/{patient_id}/users",
    summary="Get patient users",
    description="""
    ใช้สำหรับดึงรายการผู้ใช้งานที่ผูกกับผู้ป่วยตามรหัสผู้ป่วย (patient_id)
    **สิทธิ์การเข้าถึง:**
    admin: เห็นทั้งหมด ,
    relative: เห็นเฉพาะญาติผู้ป่วยเดียวกัน ,
    nurse: เห็นเฉพาะตัวเอง ญาติผู้ป่วย พยาบาลคนอื่นที่ดูแลผู้ป่วยเดียวกัน ,
    doctor: ทุกคนที่เกี่ยวข้องกับผู้ป่วยคนนี้
    """,
    response_model=list[PatientUserResponse]
)
def get_patient_users(patient_id: UUID,db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
): return PatientService.get_patient_users(db, user, patient_id)


@router.post(
    "",
    summary="Create patient",
    description="""
    สร้างผู้ป่วยใหม่ในระบบ
    **สิทธิ์การเข้าถึง:**
    เฉพาะ owner/manager ของสถานที่ดูแลเท่านั้นที่สามารถสร้างผู้ป่วยได้ โดยต้องระบุรหัสสถานที่ดูแลใน payload ด้วย
    **Payload**
    first_name(ชื่อผู้ป่วย) จำเป็น ,
    last_name(นามสกุลผู้ป่วย) จำเป็น ,
    gender(เพศผู้ป่วย) ชาย/หญิง/อื่นๆ/ไม่ระบุ จำเป็น ,
    birth_date(วันเกิดผู้ป่วย) ไม่จำเป็น ,
    weight(น้ำหนักผู้ป่วย) ไม่จำเป็น ,
    height(ส่วนสูงผู้ป่วย) ไม่จำเป็น ,
    notes(หมายเหตุ) ไม่จำเป็น ,
    facility_id(รหัสสถานที่ดูแล) จำเป็น
    """,
)
def create_patient(payload: PatientCreateRequest,db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
): return PatientService.create_patient(db, user, payload)


@router.post(
    "/{patient_id}/share",
    summary="Share patient with another user",
    description="""
    ใช้สำหรับแชร์ผู้ป่วยให้กับผู้ใช้งานอื่นผ่านทางอีเมล
    **สิทธิ์การเข้าถึง:**
    ต้องเป็นผู้ป่วยที่มีห้องอยู่ในสถานที่ดูแลเดียวกันกับผู้ใช้งานเท่านั้น
    admin: เเชร์ไม่ได้ ,
    relative/nurse/doctor: แชร์ได้ทุกบทบาทเเต่ต้องเป็นเจ้าของหรือผู้จัดการของสถานที่ที่ผู้ป่วยอยู่เท่านั้น
    **Payload** 
    email(อีเมลผู้รับเชิญ) จำเป็น
    role(บทบาทความสัมพันธ์กับผู้ป่วยที่ต้องการ) relative/nurse/doctor จำเป็น
    """,
)
def share_patient(patient_id: UUID,payload: PatientShareRequest,db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
): return PatientService.share_patient(db, user, patient_id, payload)


@router.post(
    "/share/accept",
    summary="Accept patient share invitation",
    description="""
    **สิทธิ์การเข้าถึง:**
    ทุกบทบาทสามารถรับคำเชิญได้ ยกเว้น admin
    ใช้สำหรับยอมรับคำเชิญแชร์ผู้ป่วย ต้อง login ก่อนใช้งาน
    **Query Parameters**
    token(รหัสคำเชิญ) จำเป็น
    """,
)
def accept_patient_share(token: str,db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user),
): return PatientService.accept_patient_share(db, user, token)


@router.patch(
    "/{patient_id}",
    summary="Update patient",
    description="""
    ใช้สำหรับแก้ไขข้อมูลผู้ป่วย (ไม่รวมที่อยู่)
    **สิทธิ์การเข้าถึง:**
    ต้องเป็นผู้ป่วยที่มีห้องอยู่ในสถานที่ดูแลเดียวกันกับผู้ใช้งานเท่านั้น
    admin: เเก้ไขได้ทั้งหมด ,
    relative/nurse/doctor: เเก้ไขได้เฉพาะผู้ป่วยที่เกี่ยวข้องและต้องเป็นเจ้าของหรือผู้จัดการของสถานที่ที่ผู้ป่วยอยู่เท่านั้น,
    **Payload**
    first_name(ชื่อผู้ป่วย) ไม่จำเป็น ,
    last_name(นามสกุลผู้ป่วย) ไม่จำเป็น ,
    gender(เพศผู้ป่วย) ชาย/หญิง/อื่นๆ/ไม่ระบุ ไม่จำเป็น ,
    birth_date(วันเกิดผู้ป่วย) ไม่จำเป็น ,
    weight(น้ำหนักผู้ป่วย) ไม่จำเป็น ,
    height(ส่วนสูงผู้ป่วย) ไม่จำเป็น ,
    notes(หมายเหตุ) ไม่จำเป็น ,
    """
)
def update_patient(patient_id: UUID, payload: PatientUpdateRequest,
    db: Session = Depends(get_db),user: User = Depends(get_current_active_user),
): return PatientService.update_patient(db, user, patient_id, payload)


@router.delete(
    "/{patient_id}",
    summary="Delete a patient",
    description="""
    ใช้สำหรับลบผู้ป่วยออกจากระบบตามรหัสผู้ป่วย (patient_id)
    **สิทธิ์การเข้าถึง:**
    admin, owner ของสถานที่ดูแลเดียวกันกับผู้ป่วยเท่านั้นที่สามารถลบผู้ป่วยได้
    """
)
def delete_patient(patient_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_active_user)):
    return PatientService.delete_patient(db, patient_id, user)