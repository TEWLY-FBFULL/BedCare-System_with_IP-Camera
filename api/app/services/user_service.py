from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from uuid import UUID
from app.schemas.user.base import UserUpdateRequest
from app.schemas.user.address import AddressUpdateRequest
from app.models import (
    User, Role, Address, Subdistrict, District, Province,
    Doctor, DoctorSpecialty, Nurse, NurseType, ProfessionalLevel
)

class UserService:
    @staticmethod
    def get_user_full_profile(db: Session, user_id: UUID):
        user = (
            db.query(User)
            .filter(User.user_id == user_id)
            .first()
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        role = db.query(Role).get(user.role_id)
        # -------- address --------
        address_info = None
        if user.address_id:
            addr = (
                db.query(Address, Subdistrict, District, Province)
                .join(Subdistrict, Address.subdistrict_id == Subdistrict.subdistrict_id)
                .join(District, Subdistrict.district_id == District.district_id)
                .join(Province, District.province_id == Province.province_id)
                .filter(Address.address_id == user.address_id)
                .first()
            )
            if addr:
                a, sd, d, p = addr
                address_info = {
                    "address_id": a.address_id,
                    "house_no": a.house_no,
                    "road": a.road,
                    "village": a.village,
                    "subdistrict_id": sd.subdistrict_id,
                    "subdistrict_name": sd.subdistrict_name,
                    "zip_code": sd.zip_code,
                    "district_id": d.district_id,
                    "district_name": d.district_name,
                    "province_id": p.province_id,
                    "province_name": p.province_name,
                }
        # -------- doctor --------
        doctor_profile = None
        if role.role_name == "doctor":
            doc = (
                db.query(Doctor, DoctorSpecialty, ProfessionalLevel)
                .join(DoctorSpecialty)
                .outerjoin(ProfessionalLevel)
                .filter(Doctor.doctor_id == user.user_id)
                .first()
            )
            if doc:
                d, sp, lv = doc
                doctor_profile = {
                    "specialty_id": sp.specialty_id,
                    "specialty_name": sp.specialty_name,
                    "level_id": lv.level_id if lv else None,
                    "level_name": lv.level_name if lv else None,
                    "license_no": d.license_no,
                }
        # -------- nurse --------
        nurse_profile = None
        if role.role_name == "nurse":
            nur = (
                db.query(Nurse, NurseType, ProfessionalLevel)
                .join(NurseType)
                .outerjoin(ProfessionalLevel)
                .filter(Nurse.nurse_id == user.user_id)
                .first()
            )
            if nur:
                n, nt, lv = nur
                nurse_profile = {
                    "nurse_type_id": nt.nurse_type_id,
                    "nurse_type_name": nt.nurse_type_name,
                    "level_id": lv.level_id if lv else None,
                    "level_name": lv.level_name if lv else None,
                    "license_no": n.license_no,
                }
        return {
            "user_id": user.user_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "role": role.role_name,
            "email_verified": user.email_verified,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "address": address_info,
            "doctor_profile": doctor_profile,
            "nurse_profile": nurse_profile,
        }

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID):
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        role = db.query(Role).filter(Role.role_id == user.role_id).first()
        return {
            **user.__dict__,
            "role": role.role_name if role else None
        }

    @staticmethod
    def list_users(
        db: Session,
        field: str | None = None,
        keyword: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ):
        query = (
            db.query(User, Role.role_name)
            .join(Role, Role.role_id == User.role_id)
        )
        if field and keyword:
            if field == "email":
                query = query.filter(User.email.ilike(f"%{keyword}%"))
            elif field == "first_name":
                query = query.filter(User.first_name.ilike(f"%{keyword}%"))
            elif field == "last_name":
                query = query.filter(User.last_name.ilike(f"%{keyword}%"))
            elif field == "user_id":
                query = query.filter(User.user_id == keyword)
        # role (fixed value)
        if field == "role" and role:
            query = query.filter(Role.role_name == role)
        # active / inactive
        if field == "is_active" and is_active is not None:
            query = query.filter(User.is_active == is_active)
        users = query.order_by(User.created_at.desc()).all()
        return [
            {
                "user_id": u.user_id,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "role": role_name,
                "is_active": u.is_active,
                "created_at": u.created_at,
            }
            for u, role_name in users
        ]
    
    @staticmethod
    def update_me(db: Session, user: User, payload: UserUpdateRequest):
        updated = False
        if payload.first_name is not None:
            user.first_name = payload.first_name
            updated = True
        if payload.last_name is not None:
            user.last_name = payload.last_name
            updated = True
        if payload.phone is not None:
            user.phone = payload.phone
            updated = True
        if not updated:
            return {"message": "ไม่มีข้อมูลที่เปลี่ยนแปลง"}
        db.commit()
        return {"message": "อัปเดตข้อมูลโปรไฟล์สำเร็จ"}
    
    @staticmethod
    def update_my_address(
        db: Session,
        user: User,
        payload: AddressUpdateRequest
    ):
        # if no address
        if not user.address_id:
            address = Address(
                house_no=payload.house_no,
                road=payload.road,
                village=payload.village,
                subdistrict_id=payload.subdistrict_id
            )
            db.add(address)
            db.flush()  # get address_id
            user.address_id = address.address_id
        else:
            # update old address
            address = db.query(Address).filter(
                Address.address_id == user.address_id
            ).first()
            if not address:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Address not found"
                )
            if payload.house_no is not None:
                address.house_no = payload.house_no
            if payload.road is not None:
                address.road = payload.road
            if payload.village is not None:
                address.village = payload.village
            address.subdistrict_id = payload.subdistrict_id
        db.commit()
        return {
            "message": "อัปเดตที่อยู่สำเร็จ"
        }
