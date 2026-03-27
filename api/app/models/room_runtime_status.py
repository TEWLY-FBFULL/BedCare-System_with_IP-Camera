from sqlalchemy import Column, Integer, Boolean, TIMESTAMP, ForeignKey, text
from sqlalchemy.orm import relationship
from app.core.database import Base

class RoomRuntimeStatus(Base):
    __tablename__ = "room_runtime_status"
    room_id = Column(
        Integer,
        ForeignKey("rooms.room_id", ondelete="CASCADE"),
        primary_key=True
    )
    camera_running = Column(Boolean, default=False)
    device_running = Column(Boolean, default=False)
    last_ai_run = Column(TIMESTAMP(timezone=True))
    last_env_log = Column(TIMESTAMP(timezone=True))
    room_active = Column(Boolean, default=True)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("now()")
    )
    # relationship
    room = relationship("Room", back_populates="runtime_status", uselist=False)