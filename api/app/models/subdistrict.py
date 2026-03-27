from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Subdistrict(Base):
    __tablename__ = "subdistricts"
    subdistrict_id = Column(Integer, primary_key=True, index=True)
    subdistrict_name = Column(String, nullable=False)
    zip_code = Column(String, nullable=True)
    district_id = Column(Integer, ForeignKey("districts.district_id"), nullable=False)
    # relationships
    district = relationship("District", back_populates="subdistricts")
    addresses = relationship("Address", back_populates="subdistrict")
