from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Numeric, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.enum import PostureLabelEnum
from app.core.database import Base

class SleepPostureLog(Base):
    __tablename__ = "sleep_posture_logs"
    posture_log_id = Column(Integer, primary_key=True)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sleep_sessions.session_id", ondelete="CASCADE")
    )
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"))
    posture_label = Column(PostureLabelEnum)
    confidence = Column(Numeric(4, 3))
    source = Column(String)
    captured_at = Column(TIMESTAMP(timezone=True), nullable=False)
    dominant_ratio = Column(Numeric(5, 2))
    stable_duration_sec = Column(Integer)
    confidence_avg = Column(Numeric(4, 3))
    bed_overlap_ratio = Column(Numeric(5, 2))
    person_detected = Column(Boolean, default=True)
    bed_detected = Column(Boolean, default=True)
    # relationships
    session = relationship("SleepSession", back_populates="posture_logs")
    patient = relationship("Patient")