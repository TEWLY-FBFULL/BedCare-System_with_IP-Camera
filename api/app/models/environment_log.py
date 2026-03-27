from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, Numeric, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class EnvironmentLog(Base):
    __tablename__ = "environment_logs"
    env_log_id = Column(Integer, primary_key=True)
    room_id = Column(
        Integer,
        ForeignKey("rooms.room_id", ondelete="CASCADE")
    )
    device_id = Column(
        Integer,
        ForeignKey("devices.device_id", ondelete="CASCADE")
    )
    temperature_c = Column(Numeric)
    humidity_pct = Column(Numeric)
    pressure_hpa = Column(Numeric)
    altitude_m = Column(Numeric)
    lux = Column(Numeric)
    camera_motion_state = Column(Boolean)
    radar_motion_state = Column(Boolean)
    help_voice_detected = Column(Boolean)
    emergency_button_pressed = Column(Boolean)
    captured_at = Column(TIMESTAMP(timezone=True), nullable=False)
    # relationships
    room = relationship("Room", back_populates="environment_logs")
    device = relationship("Device")