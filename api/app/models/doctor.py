from sqlalchemy import Column, ForeignKey, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class Doctor(Base):
    __tablename__ = "doctors"
    doctor_id = Column(UUID(as_uuid=True),
                       ForeignKey("users.user_id"),
                       primary_key=True)
    specialty_id = Column(Integer, ForeignKey("doctor_specialties.specialty_id"))
    level_id = Column(Integer, ForeignKey("professional_levels.level_id"))
    license_no = Column(String, unique=True)
    is_active = Column(Boolean, default=True)
