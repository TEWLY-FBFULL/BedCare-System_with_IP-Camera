from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base

class Address(Base):
    __tablename__ = "addresses"
    address_id = Column(Integer, primary_key=True, index=True)
    house_no = Column(String, nullable=True)
    road = Column(String, nullable=True)
    village = Column(String, nullable=True)
    subdistrict_id = Column(Integer, ForeignKey("subdistricts.subdistrict_id"), nullable=True)
    # relationships
    subdistrict = relationship("Subdistrict", back_populates="addresses")
    patients = relationship("Patient", back_populates="address")
    facilities = relationship("Facility", back_populates="address") 
