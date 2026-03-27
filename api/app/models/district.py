from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class District(Base):
    __tablename__ = "districts"
    district_id = Column(Integer, primary_key=True, index=True)
    district_name = Column(String, nullable=False)
    province_id = Column(Integer, ForeignKey("provinces.province_id"), nullable=False)
    # relationships
    province = relationship("Province", back_populates="districts")
    subdistricts = relationship(
        "Subdistrict",
        back_populates="district",
        cascade="all, delete-orphan"
    )
