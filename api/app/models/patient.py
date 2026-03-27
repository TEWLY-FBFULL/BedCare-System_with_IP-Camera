from sqlalchemy import Column, String, Date, Numeric, Integer, TIMESTAMP, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patients"
    patient_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    weight = Column(Numeric(5, 2), nullable=True)
    height = Column(Numeric(5, 2), nullable=True)
    notes = Column(String, nullable=True)
    address_id = Column(Integer, ForeignKey("addresses.address_id"), nullable=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("now()"),
        nullable=False
    )
    # relationships
    address = relationship("Address", back_populates="patients")
    user_links = relationship("UserPatient", back_populates="patient", cascade="all, delete-orphan")
    assignments = relationship("RoomAssignment", back_populates="patient", cascade="all, delete-orphan")
    # user share tokens
    share_tokens = relationship("PatientShareToken",back_populates="patient",cascade="all, delete-orphan")
    sleep_sessions = relationship("SleepSession", back_populates="patient")
