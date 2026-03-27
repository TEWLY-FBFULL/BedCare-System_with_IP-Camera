from sqlalchemy import Column, Integer, String
from app.core.database import Base

class DoctorSpecialty(Base):
    __tablename__ = "doctor_specialties"
    specialty_id = Column(Integer, primary_key=True, autoincrement=True)
    specialty_name = Column(String, nullable=False)
