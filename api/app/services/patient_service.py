import os
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
from uuid import UUID
from app.services.email_service import EmailService
from app.models.patient import Patient
from app.models.user_patient import UserPatient
from app.models.user import User
from app.models.patient_share_token import PatientShareToken
from app.schemas.patient.response import (
    PatientListResponse, 
    PatientUserResponse, 
    PatientDetailResponse)
from app.utils.token_generator import generate_token
from app.services.permission import (
    Action,
    get_role_name, 
    map_role_to_relation, 
    can_access_patient, 
    can_modify_patient_via_facility, 
    get_active_facilities
)

class PatientService:

    @staticmethod
    def list_patients(db: Session, user: User):
        role = get_role_name(db, user)
        base_query = db.query(Patient)
        if role == "admin":
            patients = base_query.order_by(Patient.created_at.desc()).all()
        elif role in ["relative", "nurse", "doctor"]:
            patients = (
                base_query.join(UserPatient)
                .filter(
                    UserPatient.user_id == user.user_id,
                    UserPatient.relation_type == map_role_to_relation(role)
                )
                .order_by(Patient.created_at.desc())
                .all()
            )
        else:
            patients = []
        return [PatientListResponse.from_orm(p) for p in patients]
    
    @staticmethod
    def get_patient_detail(db: Session, user: User, patient_id: UUID):
        patient = (
            db.query(Patient)
            .filter(Patient.patient_id == patient_id)
            .first()
        )
        if not patient: raise HTTPException(status_code=404, detail="ไม่พบผู้ป่วย")
        if not can_access_patient(db, user, patient_id):
            raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึงข้อมูลนี้")
        return PatientDetailResponse.from_orm(patient)
    
    @staticmethod
    def get_patient_users(db: Session, user: User, patient_id: UUID):
        if not can_access_patient(db, user, patient_id):
            raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึงข้อมูลนี้")
        role = get_role_name(db, user)
        q = (db.query(User, UserPatient.relation_type)
            .join(UserPatient, UserPatient.user_id == User.user_id)
            .filter(UserPatient.patient_id == patient_id))
        if role == "relative": q = q.filter(UserPatient.relation_type == map_role_to_relation(role))
        elif role == "nurse": q = q.filter(UserPatient.relation_type.in_(["relative", "caregiver"]))
        elif role == "doctor": q = q.filter(UserPatient.relation_type.in_(["relative", "caregiver", "doctor"]))
        # admin = no filter
        return [ PatientUserResponse(
                user_id=u.user_id,
                first_name=u.first_name,
                last_name=u.last_name,
                email=u.email,
                phone=u.phone,
                relation_type=rel
            )for u, rel in q.all()]
    
    @staticmethod
    def create_patient(db: Session, user: User, payload):
        role = get_role_name(db, user)
        if role == "admin":
            raise HTTPException(status_code=403,detail="admin ไม่สามารถสร้างผู้ป่วยได้")
        # get facilities at user active
        active_facilities = get_active_facilities(db, user)
        # select facility = payload.facility_id
        selected_uf = next(
            (uf for uf in active_facilities if uf.facility_id == payload.facility_id),
            None
        )
        if not selected_uf or selected_uf.role_in_facility not in ["owner", "manager"]:
            raise HTTPException(status_code=403,detail="ไม่พบหรือไม่มีสิทธิ์ในสถานที่ดูแลที่เลือก")
        facility = selected_uf.facility
        if not facility:
            raise HTTPException(status_code=404,detail="ไม่พบสถานที่ดูแล")
        patient = Patient(
            first_name=payload.first_name,
            last_name=payload.last_name,
            gender=payload.gender,
            birth_date=payload.birth_date,
            weight=payload.weight,
            height=payload.height,
            notes=payload.notes,
            address_id=facility.address_id
        )
        db.add(patient)
        db.flush()
        relation = map_role_to_relation(role)
        if not relation:
            raise HTTPException(status_code=400,detail="บทบาทนี้ไม่สามารถสร้างผู้ป่วยได้")
        db.add(UserPatient(
            user_id=user.user_id,
            patient_id=patient.patient_id,
            relation_type=relation
        ))
        db.commit()
        db.refresh(patient)
        return patient
    
    @staticmethod
    def share_patient(db: Session,user: User,patient_id: UUID, payload):
        if not can_access_patient(db, user, patient_id):
            raise HTTPException(403, "คุณไม่มีความเกี่ยวข้องกับผู้ป่วย")
        if not can_modify_patient_via_facility(db,user=user,patient_id=patient_id,
            action=Action.UPDATE):
            raise HTTPException(403,"เฉพาะเจ้าของหรือผู้จัดการของสถานที่ที่ผู้ป่วยอยู่เท่านั้น")
        if get_role_name(db, user) == "admin":
            raise HTTPException(status_code=403, detail="admin ไม่สามารถแชร์ผู้ป่วยได้") 
        target_role = payload.role
        target_relation = map_role_to_relation(target_role)
        if not target_relation:
            raise HTTPException(status_code=400, detail="บทบาทที่เลือกไม่ถูกต้อง")
        invitee = (
            db.query(User)
            .filter(User.email == payload.email)
            .first()
        )
        if not invitee:
            return {"message": "หากอีเมลผู้รับมีในระบบ คำเชิญจะถูกส่งไปยังอีเมลนั้น"}
        if invitee.user_id == user.user_id:
            raise HTTPException(status_code=400, detail="ไม่สามารถเชิญตัวเองได้")
        invitee_role = get_role_name(db, invitee)
        if invitee_role != target_role:
            raise HTTPException(status_code=400, detail="บทบาทของผู้รับไม่ตรงกับที่เลือก")
        exists = (
            db.query(UserPatient)
            .filter(
                UserPatient.user_id == invitee.user_id,
                UserPatient.patient_id == patient_id,
                UserPatient.relation_type == target_relation
            )
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="ผู้ใช้นี้มีความสัมพันธ์กับผู้ป่วยในบทบาทนี้อยู่แล้ว")
        token, expires_at = generate_token(180)  # 3 hours
        share = PatientShareToken(
            patient_id=patient_id,
            inviter_user_id=user.user_id,
            invitee_email=payload.email,
            relation_type=target_relation,
            token=token,
            expires_at=expires_at,
        )
        db.add(share)
        db.commit()
        frontend_url = os.getenv("REAL_FRONTEND_URL")
        share_url = f"{frontend_url}/verify-share-patient?token={token}"
        inviter_fullname = f"{user.first_name} {user.last_name}"
        role_display = target_role.capitalize()
        expire_display = expires_at.strftime("%d %B %Y %H:%M")
        EmailService.send_patient_share_email(
            email=payload.email, 
            share_url=share_url,
            inviter_name=inviter_fullname,
            role_name=role_display,
            expires_at=expire_display
        )
        return {"message": "หากอีเมลผู้รับมีในระบบ คำเชิญจะถูกส่งไปยังอีเมลนั้น"}
    
    @staticmethod
    def accept_patient_share(db: Session, user: User, token: str):
        if get_role_name(db, user) == "admin":
            raise HTTPException(403, "admin ไม่สามารถรับคำเชิญได้")
        now_utc = datetime.now(timezone.utc)
        share = (
            db.query(PatientShareToken).filter(
                PatientShareToken.token == token,
                PatientShareToken.used_at.is_(None),
                PatientShareToken.expires_at > now_utc
            ).first()
        )
        if not share: raise HTTPException(400, "ลิงก์ไม่ถูกต้องหรือหมดอายุ")
        if user.email != share.invitee_email: raise HTTPException(403, "อีเมลไม่ตรงกับคำเชิญ")
        if map_role_to_relation(get_role_name(db, user)) != share.relation_type:
            raise HTTPException(status_code=403,detail="บทบาทไม่ตรงกับคำเชิญ")
        # prevent duplicate link
        exists = (db.query(UserPatient)
            .filter(
                UserPatient.user_id == user.user_id,
                UserPatient.patient_id == share.patient_id,
                UserPatient.relation_type == share.relation_type
            ).first()
        )
        if exists: 
            raise HTTPException(status_code=400,detail="คุณมีความสัมพันธ์กับผู้ป่วยนี้แล้ว")
        db.add(UserPatient(
            user_id=user.user_id,
            patient_id=share.patient_id,
            relation_type=share.relation_type
            # uspa_id auto
        ))
        share.used_at = now_utc
        db.commit()
        return {"message": "เชื่อมโยงผู้ป่วยเรียบร้อยแล้ว"}
    
    @staticmethod
    def update_patient(db: Session,user: User,patient_id: UUID,payload):
        if not can_access_patient(db, user, patient_id):
            raise HTTPException(status_code=403,detail="ไม่มีสิทธิ์เข้าถึงข้อมูลนี้")
        if not can_modify_patient_via_facility(db,user=user,patient_id=patient_id,
            action=Action.UPDATE):
            raise HTTPException(403,"เฉพาะเจ้าของหรือผู้จัดการของสถานที่ที่ผู้ป่วยอยู่เท่านั้น")
        patient = (
            db.query(Patient).filter(Patient.patient_id == patient_id).first()
        )
        if not patient: raise HTTPException(status_code=404,detail="ไม่พบผู้ป่วย")
        # update only provided fields
        update_data = payload.dict(exclude_unset=True)
        for field, value in update_data.items(): setattr(patient, field, value)
        db.commit()
        db.refresh(patient)
        return patient
    
    @staticmethod
    def delete_patient(db: Session, patient_id: UUID, user: User):
        if not can_modify_patient_via_facility(db,user=user,patient_id=patient_id,
            action=Action.DELETE):
            raise HTTPException(403,"เฉพาะเจ้าของสถานที่ที่ผู้ป่วยอยู่เท่านั้น")
        patient = (
            db.query(Patient)
            .filter(Patient.patient_id == patient_id)
            .first()
        )
        if not patient: raise HTTPException(status_code=404, detail="ไม่พบผู้ป่วย")
        db.delete(patient)
        db.commit()
        return {"message": "ผู้ป่วยถูกลบเรียบร้อยแล้ว"}