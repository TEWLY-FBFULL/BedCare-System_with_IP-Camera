from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum as PgEnum
from app.core.database import Base

auth_type_enum = PgEnum(
    "Digest/Basic", "Basic",
    name="auth_type_enum"
)

class CameraBrand(Base):
    __tablename__ = "camera_brands"
    brand_id = Column(Integer, primary_key=True, autoincrement=True)
    brand_name = Column(String, nullable=False)
    rtsp_pattern = Column(String, nullable=True)
    auth_type = Column(auth_type_enum, nullable=True)
    # relationships
    cameras = relationship("Camera", back_populates="brand")
