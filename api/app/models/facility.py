from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.enum import FacilityTypeEnum
from app.core.database import Base

class Facility(Base):
    __tablename__ = "facilities"
    facility_id = Column(Integer, primary_key=True, autoincrement=True)
    facility_name = Column(String, nullable=False)
    facility_type = Column(FacilityTypeEnum, nullable=True)
    address_id = Column(Integer, ForeignKey("addresses.address_id"), nullable=False)
    # relationships
    address = relationship("Address", back_populates="facilities")
    rooms = relationship("Room", back_populates="facility", cascade="all, delete-orphan")
    user_links = relationship("UserFacility", back_populates="facility", cascade="all, delete-orphan")
    share_tokens = relationship(
        "FacilityShareToken",
        back_populates="facility",
        cascade="all, delete-orphan"
    )