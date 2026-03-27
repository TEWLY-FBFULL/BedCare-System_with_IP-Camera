import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
from sqlalchemy import (Column, Integer, Text,ForeignKey, TIMESTAMP, text, CheckConstraint)

class FacilityShareToken(Base):
    __tablename__ = "facility_share_tokens"
    __table_args__ = (
        CheckConstraint(
            "role_in_facility IN ("
            "'doctor', 'nurse', 'caregiver', 'manager'"
            ")",
            name="ck_facility_share_tokens_role"
        ),
    )
    share_token_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    facility_id = Column(
        Integer,
        ForeignKey("facilities.facility_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    inviter_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    invitee_email = Column(Text, nullable=False)
    role_in_facility = Column(Text, nullable=False)
    token = Column(Text, nullable=False, unique=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    used_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("now()")
    )
    # relationships
    facility = relationship("Facility", back_populates="share_tokens")
    inviter = relationship("User", back_populates="sent_facility_share_tokens")