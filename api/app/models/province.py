from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class Province(Base):
    __tablename__ = "provinces"
    province_id = Column(Integer, primary_key=True, index=True)
    province_name = Column(String, nullable=False)
    # relationships
    districts = relationship(
        "District",
        back_populates="province",
        cascade="all, delete-orphan"
    )
