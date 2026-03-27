from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, TIMESTAMP, text
from sqlalchemy.orm import relationship
from app.core.database import Base

class Device(Base):
    __tablename__ = "devices"
    device_id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(
        Integer,
        ForeignKey("rooms.room_id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    device_name = Column(String)
    device_token = Column(
        String,
        unique=True,
        nullable=False
    )
    is_active = Column(Boolean, default=True)
    last_seen_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("now()"),
        nullable=False
    )
    # Define relationship to Room
    room = relationship("Room",back_populates="device",uselist=False)
    sensors = relationship("Sensor", back_populates="device", cascade="all, delete-orphan")