from sqlalchemy.orm import Session
from fastapi import HTTPException
from uuid import UUID
from app.models.user import User
from app.models.role import Role
from app.models.room import Room
from app.models.user_patient import UserPatient
from app.models.user_facility import UserFacility
from app.models.room_assignment import RoomAssignment
from enum import Enum

class Action(str, Enum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ASSIGN = "assign"

def get_role_name(db: Session, user: User) -> str:
    role = db.query(Role).filter(Role.role_id == user.role_id).first()
    return role.role_name if role else ""

def get_role_name_in_facility(db: Session,user: User,facility_id: int) -> str:
    link = (
        db.query(UserFacility)
        .filter(
            UserFacility.user_id == user.user_id,
            UserFacility.facility_id == facility_id,
            UserFacility.is_active == True
        )
        .first()
    )
    return link.role_in_facility if link else ""

def map_role_to_relation(role: str) -> str | None:
    return {
        "relative": "relative",
        "nurse": "caregiver",
        "doctor": "doctor",
    }.get(role)

def can_access_patient(db: Session, user: User, patient_id: UUID) -> bool:
    role = get_role_name(db, user)
    # admin = full access
    if role == "admin": return True
    # relative / nurse / doctor via user_patient
    return db.query(UserPatient).filter(
        UserPatient.user_id == user.user_id,
        UserPatient.patient_id == patient_id
    ).first() is not None

def get_active_facilities(db: Session, user: User) -> list[UserFacility]:
    ufs = db.query(UserFacility).filter(
        UserFacility.user_id == user.user_id,
        UserFacility.is_active.is_(True)
    ).all()
    if not ufs:
        raise HTTPException(403, "ผู้ใช้ต้องสังกัดสถานที่ดูแลก่อน")
    return ufs

def can_access_facility(db: Session,*,user_id: UUID,facility_id: int,action: Action) -> bool:
    uf = (
        db.query(UserFacility)
        .filter(
            UserFacility.user_id == user_id,
            UserFacility.facility_id == facility_id,
            UserFacility.is_active.is_(True)
        )
        .first()
    )
    if not uf:
        return False
    role = uf.role_in_facility
    if action == Action.READ:
        return True
    if action in [Action.CREATE, Action.UPDATE]:
        return role in ["owner", "manager"]
    if action == Action.ASSIGN:
        return role in ["owner","manager"]
    if action == Action.DELETE:
        return role == "owner"
    return False

def can_modify_patient_via_facility(db: Session,*,user: User,patient_id: UUID,
    action: Action = Action.UPDATE) -> bool:
    # select facility from current room assignment
    assignment = (
        db.query(RoomAssignment)
        .join(Room, Room.room_id == RoomAssignment.room_id)
        .filter(
            RoomAssignment.patient_id == patient_id,
            RoomAssignment.discharged_at.is_(None)
        )
        .first()
    )
    if not assignment:
        return False  # patient not currently in any facility
    facility_id = assignment.room.facility_id
    # check user to have this facility
    return can_access_facility(
        db,
        user_id=user.user_id,
        facility_id=facility_id,
        action=action
    )

def can_access_room(db: Session,*,user_id: UUID,room_id: int,action: Action) -> bool:
    room = db.query(Room).filter(Room.room_id == room_id).first()
    if not room: return False
    return can_access_facility(
        db,
        user_id=user_id,
        facility_id=room.facility_id,
        action=action
    )

def can_read_room_patient_context(db: Session,*,user: User,room_id: int) -> bool:
    # Admin can access all rooms regardless of facility or patient context
    role = get_role_name(db, user)
    if role == "admin": return True
    # Search room + facility
    room = db.query(Room).filter(Room.room_id == room_id).first()
    if not room: return False
    facility_role = get_role_name_in_facility(
        db, user, room.facility_id
    )
    # owner / manager 
    if facility_role in ["owner", "manager"]: return True
    # Search active patient in room 
    assignment = (
        db.query(RoomAssignment)
        .filter(
            RoomAssignment.room_id == room_id,
            RoomAssignment.discharged_at.is_(None)
        )
        .first()
    )
    if not assignment: return False
    # User has access to patient in room
    return can_access_patient(
        db,
        user=user,
        patient_id=assignment.patient_id
    )

def get_alert_recipients(db: Session, facility_id: int, patient_id: UUID | None) -> list[str]:
    emails = []
    for role in ["manager", "doctor", "nurse"]:
        user = db.query(User).join(UserFacility).filter(
            UserFacility.facility_id == facility_id,
            UserFacility.is_active == True,
            UserFacility.role_in_facility == role
        ).first()
        if user and user.email:
            emails.append(user.email)
            
    if "manager" not in [u.role_in_facility for u in db.query(UserFacility).filter(UserFacility.facility_id == facility_id, UserFacility.is_active == True).all()]:
        owner = db.query(User).join(UserFacility).filter(
            UserFacility.facility_id == facility_id,
            UserFacility.role_in_facility == "owner",
            UserFacility.is_active == True
        ).first()
        if owner and owner.email:
            emails.append(owner.email)

    if patient_id:
        caregiver = db.query(User).join(UserPatient).filter(
            UserPatient.patient_id == patient_id
        ).first()
        if caregiver and caregiver.email:
            emails.append(caregiver.email)
    return list(set(emails))