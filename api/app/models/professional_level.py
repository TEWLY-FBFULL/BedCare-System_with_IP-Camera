from sqlalchemy import Column, Integer, String
from app.core.database import Base

class ProfessionalLevel(Base):
    __tablename__ = "professional_levels"
    level_id = Column(Integer, primary_key=True, autoincrement=True)
    level_name = Column(String, nullable=False)
