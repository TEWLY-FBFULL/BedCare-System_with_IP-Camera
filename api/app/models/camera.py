from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship
from app.core.database import Base

class Camera(Base):
    __tablename__ = "cameras"
    camera_id = Column(Integer, primary_key=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("camera_brands.brand_id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.room_id"), unique=True, nullable=False)
    ip_address = Column(INET, nullable=False)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    # relationships
    brand = relationship("CameraBrand", back_populates="cameras")
    room = relationship("Room", back_populates="camera")