from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from datetime import datetime, timezone
from app.models.user import User
from app.models.room import Room
from app.models.room_assignment import RoomAssignment
from app.models.room_runtime_status import RoomRuntimeStatus
from app.schemas.room.response import RoomDetailOut, RoomPatientDetail
from app.models.patient import Patient
from app.services.permission import (
    can_access_facility, 
    Action, 
    get_role_name,
    can_access_room,
    can_access_patient,
    get_role_name_in_facility
)

class RoomService:

    @staticmethod
    def get(db: Session, *, user: User, room_id: int):
        if not can_access_room(
            db, user_id=user.user_id, room_id=room_id, action=Action.READ
        ) and get_role_name(db, user) != "admin":
            raise HTTPException(403, "ไม่มีสิทธิ์เข้าถึงห้องหรือไม่พบห้อง")
        room = db.query(Room).filter(Room.room_id == room_id).first()
        if not room:
            raise HTTPException(404, "ไม่พบห้อง")
        assignment = (
            db.query(RoomAssignment)
            .join(Patient)
            .filter(
                RoomAssignment.room_id == room_id,
                RoomAssignment.discharged_at.is_(None)
            )
            .first()
        )
        if not assignment:
            return RoomDetailOut(
                room_id=room.room_id,
                room_number=room.room_number,
                facility_id=room.facility_id,
                is_occupied=False,
                patient=None
            )
        patient = assignment.patient
        can_view_full = (
            get_role_name(db, user) == "admin"
            or get_role_name_in_facility(db, user, room.facility_id) in ["owner", "manager"]
            or can_access_patient(db, user, patient.patient_id)
        )
        patient_data = RoomPatientDetail(
            patient_id=patient.patient_id,
            first_name=patient.first_name,
            last_name=patient.last_name,
            gender=patient.gender if can_view_full else None,
            birth_date=patient.birth_date if can_view_full else None,
            weight=patient.weight if can_view_full else None,
            height=patient.height if can_view_full else None,
            notes=patient.notes if can_view_full else None,
            address_id=patient.address_id if can_view_full else None,
            assigned_at=assignment.assigned_at
        )
        return RoomDetailOut(
            room_id=room.room_id,
            room_number=room.room_number,
            facility_id=room.facility_id,
            is_occupied=True,
            patient=patient_data
        )

    @staticmethod
    def create(db: Session, *, user: User, payload):
        if not can_access_facility(
            db,
            user_id=user.user_id,
            facility_id=payload.facility_id,
            action=Action.CREATE
        ):
            raise HTTPException(403,"ไม่มีสิทธิ์สร้างห้องหรือไม่พบสถานที่ดูแล")
        room = Room(
            room_number=payload.room_number,
            facility_id=payload.facility_id
        )
        db.add(room)
        db.flush()
        runtime = RoomRuntimeStatus(
            room_id=room.room_id,
            camera_running=False,
            device_running=False,
            room_active=True
        )
        db.add(runtime)
        db.commit()
        db.refresh(room)
        return room
    
    @staticmethod
    def update(db: Session,*,user: User,room_id: int,payload):
        if not can_access_room(db,user_id=user.user_id,
            room_id=room_id,action=Action.UPDATE
        ):
            raise HTTPException(403,"ไม่มีสิทธิ์แก้ไขห้องหรือไม่พบห้อง")
        room = db.query(Room).filter(Room.room_id == room_id).first()
        if not room:
            raise HTTPException(404,"ไม่พบห้อง")
        for k,v in payload.dict(exclude_unset=True).items():
            setattr(room,k,v)
        db.commit()
        db.refresh(room)
        return room
    
    @staticmethod
    def assign_patient(db: Session, *, user: User,room_id: int, payload):
        if not can_access_room(db, user_id=user.user_id,
            room_id=room_id, action=Action.ASSIGN
        ): raise HTTPException(403,"ไม่มีสิทธิ์กำหนดห้องให้ผู้ป่วยหรือไม่พบห้อง")
        # check if room is occupied
        room_occupied = db.query(RoomAssignment).filter(
            RoomAssignment.room_id == room_id,
            RoomAssignment.discharged_at.is_(None)
        ).first()
        if room_occupied: raise HTTPException(400, "ห้องนี้มีผู้ป่วยอยู่แล้ว")
        # discharge old assignment
        current = db.query(RoomAssignment).filter(
            RoomAssignment.patient_id == payload.patient_id,
            RoomAssignment.discharged_at.is_(None)
        ).first()
        if current and current.room_id == room_id:
            raise HTTPException(400, "ผู้ป่วยอยู่ห้องนี้อยู่แล้ว")
        if current:
            current.discharged_at = datetime.now(timezone.utc)
        assignment = RoomAssignment(
            patient_id=payload.patient_id,
            room_id=room_id,
            assigned_at=datetime.now(timezone.utc),
            assigned_by=user.user_id,
            note=payload.note
        )
        db.add(assignment)
        try:
            db.commit()
            db.refresh(assignment)
            return {"message":"assign สำเร็จ"}
        except IntegrityError:
            db.rollback()
            raise HTTPException(400, "ห้องนี้ถูกใช้งานไปแล้ว")
        
    @staticmethod
    def delete(db: Session, *, user: User, room_id: int):
        if not can_access_room(
            db,
            user_id=user.user_id,
            room_id=room_id,
            action=Action.DELETE
        ) and get_role_name(db, user) != "admin":
            raise HTTPException(403, "ไม่มีสิทธิ์")
        room = db.query(Room).filter(
            Room.room_id == room_id
        ).first()
        if not room:
            raise HTTPException(404, "ไม่พบห้อง")
        db.delete(room)
        db.commit()
        return {"message": "ลบห้องสำเร็จ"}