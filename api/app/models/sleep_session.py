from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class SleepSession(Base):
    __tablename__ = "sleep_sessions"
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id"))
    room_id = Column(Integer, ForeignKey("rooms.room_id", ondelete="CASCADE"))
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True))
    avg_sleep_score = Column(Numeric(5, 2))
    dominant_posture = Column(String)
    status = Column(String, default="active")
    duration_sec = Column(Integer)
    # relationships
    patient = relationship("Patient", back_populates="sleep_sessions")
    room = relationship("Room", back_populates="sleep_sessions")
    posture_logs = relationship(
        "SleepPostureLog",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    metric_logs = relationship(
        "SleepMetricLog",
        back_populates="session",
        cascade="all, delete-orphan"
    )