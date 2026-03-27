from sqlalchemy import Column, String, Boolean, ForeignKey, TIMESTAMP, Integer, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.address_id"))
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String)
    password_hash = Column(String, nullable=False)
    email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"),nullable=False)
    token_version = Column(Integer, nullable=False, default=1)
    # relationships
    patient_links = relationship("UserPatient",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    facility_links = relationship("UserFacility",
    back_populates="user",
    cascade="all, delete-orphan"
    )
    sent_share_tokens = relationship("PatientShareToken",
        back_populates="inviter",
        cascade="all, delete-orphan"
    )
    sent_facility_share_tokens = relationship("FacilityShareToken",
        back_populates="inviter",
        cascade="all, delete-orphan"
    )