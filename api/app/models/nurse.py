from sqlalchemy import Column, ForeignKey, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Nurse(Base):
    __tablename__ = "nurses"
    nurse_id = Column(UUID(as_uuid=True),
                      ForeignKey("users.user_id"),
                      primary_key=True)
    nurse_type_id = Column(Integer, ForeignKey("nurse_types.nurse_type_id"))
    level_id = Column(Integer, ForeignKey("professional_levels.level_id"))
    license_no = Column(String, unique=True)
    is_active = Column(Boolean, default=True)
