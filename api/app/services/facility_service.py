import os
from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from app.models.facility import Facility
from app.models.user_facility import UserFacility
from app.models.facility_share_token import FacilityShareToken
from app.models.user import User
from app.models.address import Address
from app.models.room import Room
from app.models.patient import Patient
from app.models.room_assignment import RoomAssignment
from app.schemas.facility.response import FacilityAllRoomOut, FacilityOut, RoomPatientInfo, RoomOut
from app.services.permission import (
    can_access_facility, 
    Action, 
    get_role_name
)
from app.services.email_service import EmailService
from app.utils.token_generator import generate_token
from app.helper.address import get_full_address
from uuid import UUID

class FacilityService:

    @staticmethod
    def list_for_user(db: Session, user: User):
        query = db.query(Facility)
        if get_role_name(db, user) != "admin":
            query = (
                query
                .join(UserFacility, Facility.facility_id == UserFacility.facility_id)
                .filter(
                    UserFacility.user_id == user.user_id,
                    UserFacility.is_active.is_(True)
                )
            )
        facilities = query.all()
        if not facilities: raise HTTPException(403, "ผู้ใช้ต้องสังกัดสถานที่ดูแลก่อน")
        result = []
        for f in facilities:
            address_info = None
            if f.address_id:
                address_info = get_full_address(db, f.address_id)
            result.append(
                FacilityOut(
                    facility_id=f.facility_id,
                    facility_name=f.facility_name,
                    facility_type=f.facility_type,
                    address=address_info
                )
            )
        return result

    @staticmethod
    def get(db: Session, *, user: User, facility_id: int):
        if not can_access_facility(db, user_id=user.user_id, facility_id=facility_id,
        action=Action.READ) and get_role_name(db, user) != "admin": 
            raise HTTPException(403, "ไม่มีสิทธิ์เข้าถึงสถานที่ดูแลนี้")
        facility = db.query(Facility).filter(
            Facility.facility_id == facility_id
        ).first()
        if not facility: raise HTTPException(404, "ไม่พบสถานที่ดูแล")
        address_info = None
        if facility.address_id:
            address_info = get_full_address(db, facility.address_id)
        return FacilityOut(
            facility_id=facility.facility_id,
            facility_name=facility.facility_name,
            facility_type=facility.facility_type,
            address=address_info
        )
    
    @staticmethod
    def get_rooms(db: Session, *, user: User, facility_id: int):
        if not can_access_facility(db,user_id=user.user_id,
            facility_id=facility_id,action=Action.READ
        ) and get_role_name(db, user) != "admin":
            raise HTTPException(403, "ไม่มีสิทธิ์เข้าถึงสถานที่ดูแลนี้")
        facility = (
            db.query(Facility)
            .filter(Facility.facility_id == facility_id)
            .first()
        )
        if not facility: raise HTTPException(404, "ไม่พบสถานที่ดูแล")
        rooms = (
            db.query(Room)
            .filter(Room.facility_id == facility_id)
            .all()
        )
        assignments = (
            db.query(RoomAssignment)
            .join(Room, Room.room_id == RoomAssignment.room_id)
            .join(Patient, Patient.patient_id == RoomAssignment.patient_id)
            .filter(
                Room.facility_id == facility_id,
                RoomAssignment.discharged_at.is_(None)
            ).all()
        )
        assignment_map = { a.room_id: a for a in assignments }
        result_rooms = []
        for room in rooms:
            assignment = assignment_map.get(room.room_id)
            if assignment:
                patient = assignment.patient
                result_rooms.append(
                    RoomOut(
                        room_id=room.room_id,
                        room_number=room.room_number,
                        is_occupied=True,
                        patient=RoomPatientInfo(
                            patient_id=patient.patient_id,
                            first_name=patient.first_name,
                            last_name=patient.last_name,
                            assigned_at=assignment.assigned_at
                        )
                    )
                )
            else:
                result_rooms.append(
                    RoomOut(
                        room_id=room.room_id,
                        room_number=room.room_number,
                        is_occupied=False,
                        patient=None
                    )
                )
        address_info = None
        if facility.address_id:
            address_info = get_full_address(db, facility.address_id)
        return FacilityAllRoomOut(
            facility_id=facility.facility_id,
            facility_name=facility.facility_name,
            facility_type=facility.facility_type,
            address=address_info,
            rooms=result_rooms
        )

    @staticmethod
    def create(db: Session, *, user_id: UUID, payload):
        if payload.address_id is None and payload.address is None:
            raise HTTPException(
                status_code=400,
                detail="ต้องระบุว่าใช้ที่อยู่ของคุณหรือที่อยู่ใหม่"
            )
        if payload.address is not None:
            new_address = Address(**payload.address.dict())
            db.add(new_address)
            db.flush()
            address_id = new_address.address_id
        else:
            address_id = payload.address_id
        facility = Facility(
            facility_name=payload.facility_name,
            facility_type=payload.facility_type,
            address_id=address_id
        )
        db.add(facility)
        db.flush()
        db.add(UserFacility(
            user_id=user_id,
            facility_id=facility.facility_id,
            role_in_facility="owner",
            is_active=True
        ))
        db.commit()
        db.refresh(facility)
        return {"message": "สร้างสถานที่ดูแลสำเร็จ"}

    @staticmethod
    def update(db: Session, *, user_id: UUID, facility_id: int, payload):
        if not can_access_facility(
            db,
            user_id=user_id,
            facility_id=facility_id,
            action=Action.UPDATE
        ):
            raise HTTPException(403, "ไม่มีสิทธิ์แก้ไขสถานที่ดูแล")
        facility = db.query(Facility).filter(
            Facility.facility_id == facility_id
        ).first()
        if not facility:
            raise HTTPException(404, "ไม่พบสถานที่ดูแล")
        for k, v in payload.dict(exclude_unset=True).items():
            setattr(facility, k, v)
        db.commit()
        db.refresh(facility)
        return {"message": "อัปเดตสถานที่ดูแลสำเร็จ"}

    @staticmethod
    def delete(db: Session, *, user: User, facility_id: int):
        if not can_access_facility(
            db,
            user_id=user.user_id,
            facility_id=facility_id,
            action=Action.DELETE
        ) and get_role_name(db, user) != "admin":
            raise HTTPException(403, "คุณไม่มีสิทธิ์ลบสถานที่ดูแลนี้")
        facility = db.query(Facility).filter(
            Facility.facility_id == facility_id
        ).first()
        if not facility:
            raise HTTPException(404, "ไม่พบสถานที่ดูแล")
        db.delete(facility)
        db.commit()
        return {"message": "ลบสถานที่ดูแลสำเร็จ"}
    
    @staticmethod
    def update_address(db: Session,*,user: User,facility_id: int,payload):
        if not can_access_facility(
            db,
            user_id=user.user_id,
            facility_id=facility_id,
            action=Action.UPDATE
        ):
            raise HTTPException(403, "ไม่มีสิทธิ์แก้ไขที่อยู่")
        facility = db.query(Facility).filter(
            Facility.facility_id == facility_id
        ).first()
        if not facility:
            raise HTTPException(404, "ไม่พบสถานที่")
        data = payload.dict(exclude_unset=True)
        if not facility.address_id:
            address = Address(**data)
            db.add(address)
            db.flush()
            facility.address_id = address.address_id
        else:
            address = db.query(Address).filter(
                Address.address_id == facility.address_id
            ).first()
            if not address:
                raise HTTPException(404, "ไม่พบข้อมูลที่อยู่")
            for k, v in data.items():
                setattr(address, k, v)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(400, "ข้อมูลที่อยู่ไม่ถูกต้อง")
        return {"message": "อัปเดตที่อยู่สำเร็จ"}
    
    @staticmethod
    def share_facility(db: Session,*,user: User,facility_id: int, payload):
        if not can_access_facility(
            db,
            user_id=user.user_id,
            facility_id=facility_id,
            action=Action.UPDATE
        ):
            raise HTTPException(403, "ไม่มีสิทธิ์แชร์สถานที่นี้")
        invitee = db.query(User).filter(
            User.email == payload.email
        ).first()
        if not invitee:
            return {"message": "หากอีเมลมีในระบบ คำเชิญจะถูกส่งไป"}
        if invitee.user_id == user.user_id:
            raise HTTPException(400, "ไม่สามารถเชิญตัวเองได้")
        exists = db.query(UserFacility).filter(
            UserFacility.user_id == invitee.user_id,
            UserFacility.facility_id == facility_id
        ).first()
        if exists:
            raise HTTPException(400, "ผู้ใช้นี้อยู่ในสถานที่แล้ว")
        if not payload.role_in_facility in ["doctor", "nurse", "caregiver", "manager"]:
            raise HTTPException(400, "บทบาทในสถานที่ไม่ถูกต้อง")
        token, expires_at = generate_token(180)
        share = FacilityShareToken(
            facility_id=facility_id,
            inviter_user_id=user.user_id,
            invitee_email=payload.email,
            role_in_facility=payload.role_in_facility,
            token=token,
            expires_at=expires_at
        )
        db.add(share)
        db.commit()
        FRONTEND_URL = os.getenv("REAL_FRONTEND_URL")
        share_url = f"{FRONTEND_URL}/verify-share?token={token}"
        inviter_name = f"{user.first_name} {user.last_name}"
        facility = db.query(Facility).filter(
            Facility.facility_id == facility_id).first()
        facility_name = facility.facility_name if facility else "ไม่ระบุ"
        role_display = payload.role_in_facility
        expire_display = expires_at.strftime("%d %B %Y %H:%M")
        EmailService.send_facility_share_email(
            email=payload.email,
            share_url=share_url,
            inviter_name=inviter_name,
            facility_name=facility_name,
            role_name=role_display,
            expires_at=expire_display
        )
        return {"message": "หากอีเมลมีในระบบ คำเชิญจะถูกส่งไป"}
    
    @staticmethod
    def accept_facility_share(db: Session,*,user: User,token: str):
        now_utc = datetime.now(timezone.utc)
        share = db.query(FacilityShareToken).filter(
            FacilityShareToken.token == token,
            FacilityShareToken.used_at.is_(None),
            FacilityShareToken.expires_at > now_utc
        ).first()
        if not share:
            raise HTTPException(400, "ลิงก์ไม่ถูกต้องหรือหมดอายุ")
        if user.email != share.invitee_email:
            raise HTTPException(403, "อีเมลไม่ตรงกับคำเชิญ")
        exists = db.query(UserFacility).filter(
            UserFacility.user_id == user.user_id,
            UserFacility.facility_id == share.facility_id
        ).first()
        if exists:
            raise HTTPException(400, "คุณอยู่ในสถานที่นี้แล้ว")
        db.add(UserFacility(
            user_id=user.user_id,
            facility_id=share.facility_id,
            role_in_facility=share.role_in_facility,
            is_active=True
        ))
        share.used_at = now_utc
        db.commit()
        return {"message": "เข้าร่วมสถานที่สำเร็จ"}
    