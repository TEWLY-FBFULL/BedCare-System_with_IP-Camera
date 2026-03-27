from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Room(Base):
    __tablename__ = "rooms"
    room_id = Column(Integer, primary_key=True, autoincrement=True)
    room_number = Column(String, nullable=False)
    facility_id = Column(Integer, ForeignKey("facilities.facility_id"), nullable=False)
    # relationships
    facility = relationship("Facility", back_populates="rooms")
    assignments = relationship("RoomAssignment", back_populates="room", cascade="all, delete-orphan")
    camera = relationship("Camera", back_populates="room", uselist=False, cascade="all, delete-orphan")
    device = relationship("Device",back_populates="room",uselist=False,cascade="all, delete-orphan")
    sleep_sessions = relationship(
        "SleepSession",
        back_populates="room",
        cascade="all, delete-orphan"
    )
    environment_logs = relationship(
        "EnvironmentLog",
        back_populates="room",
        cascade="all, delete-orphan"
    )
    alert_logs = relationship(
        "AlertLog",
        back_populates="room",
        cascade="all, delete-orphan"
    )
    runtime_status = relationship(
        "RoomRuntimeStatus",
        back_populates="room",
        uselist=False,
        cascade="all, delete-orphan"
    )