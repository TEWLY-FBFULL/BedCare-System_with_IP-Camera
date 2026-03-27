from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, Boolean, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.enum import AlertTypeEnum, SeverityEnum
from app.core.database import Base

class AlertLog(Base):
    __tablename__ = "alert_logs"
    alert_id = Column(Integer, primary_key=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"))
    room_id = Column(
        Integer,
        ForeignKey("rooms.room_id", ondelete="CASCADE")
    )
    alert_type = Column(AlertTypeEnum)
    severity = Column(SeverityEnum)
    trigger_source = Column(String)
    trigger_value = Column(String)
    message = Column(String)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(TIMESTAMP(timezone=True))
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("now()")
    )
    resolved_at = Column(TIMESTAMP(timezone=True))
    resolution_note = Column(String)
    # relationships
    patient = relationship("Patient")
    room = relationship("Room", back_populates="alert_logs")
    acknowledged_user = relationship("User")