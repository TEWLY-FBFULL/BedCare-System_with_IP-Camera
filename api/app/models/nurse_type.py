from sqlalchemy import Column, Integer, String
from app.core.database import Base

class NurseType(Base):
    __tablename__ = "nurse_types"
    nurse_type_id = Column(Integer, primary_key=True, autoincrement=True)
    nurse_type_name = Column(String, nullable=False)
