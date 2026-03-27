from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, String, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class RoomAssignment(Base):
    __tablename__ = "room_assignments"
    __table_args__ = (
        CheckConstraint(
            "discharged_at IS NULL OR discharged_at > assigned_at",
            name="ck_room_assignments_time"
        ),
    )
    assignment_id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.room_id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(TIMESTAMP(timezone=True), nullable=False)
    discharged_at = Column(TIMESTAMP(timezone=True), nullable=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    note = Column(String, nullable=True)
    # relationships
    patient = relationship("Patient", back_populates="assignments")
    room = relationship("Room", back_populates="assignments")
    assigned_user = relationship("User")
