from sqlalchemy import (
    Column,
    Integer,
    Boolean,
    ForeignKey,
    Text,
    TIMESTAMP,
    CheckConstraint,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserFacility(Base):
    __tablename__ = "user_facilities"
    __table_args__ = (
        UniqueConstraint("user_id", "facility_id", name="uq_user_facility"),
        CheckConstraint(
            "role_in_facility IN ("
            "'doctor', 'nurse', 'caregiver', 'owner', 'manager'"
            ")",
            name="ck_user_facility_role"
        ),
    )
    uf_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True),ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    facility_id = Column(Integer,ForeignKey("facilities.facility_id", ondelete="CASCADE"),
        nullable=False
    )
    role_in_facility = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    joined_at = Column(TIMESTAMP(timezone=True),server_default=text("now()"),nullable=False)
    # relationships
    user = relationship("User", back_populates="facility_links")
    facility = relationship("Facility", back_populates="user_links")