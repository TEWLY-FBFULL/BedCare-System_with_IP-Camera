from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.enum import PostureQualityEnum
from app.core.database import Base

class SleepMetricLog(Base):
    __tablename__ = "sleep_metric_logs"
    metric_log_id = Column(Integer, primary_key=True)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sleep_sessions.session_id", ondelete="CASCADE")
    )
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"))
    posture_quality = Column(PostureQualityEnum)
    captured_at = Column(TIMESTAMP(timezone=True), nullable=False)
    neck_tilt_avg = Column(Numeric)
    neck_tilt_max = Column(Numeric)
    trunk_flex_avg = Column(Numeric)
    trunk_flex_max = Column(Numeric)
    axial_rotation_avg = Column(Numeric)
    axial_rotation_max = Column(Numeric)
    body_tilt_avg = Column(Numeric)
    body_tilt_max = Column(Numeric)
    neck_flex_avg = Column(Numeric)
    neck_flex_max = Column(Numeric)
    lateral_tilt_avg = Column(Numeric)
    lateral_tilt_max = Column(Numeric)
    head_rotation_avg = Column(Numeric)
    head_rotation_max = Column(Numeric)
    posture_score_avg = Column(Numeric)
    risk_flag = Column(Boolean, default=False)
    # relationships
    session = relationship("SleepSession", back_populates="metric_logs")
    patient = relationship("Patient")