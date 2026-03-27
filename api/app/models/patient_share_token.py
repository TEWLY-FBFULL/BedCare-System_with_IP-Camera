import uuid
from sqlalchemy import (Column, Text, TIMESTAMP, ForeignKey)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship
from app.models.enum import relation_type_enum
from app.core.database import Base

class PatientShareToken(Base):
    __tablename__ = "patient_share_tokens"
    share_token_id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True),
        ForeignKey("patients.patient_id", ondelete="CASCADE"),
        nullable=False)
    inviter_user_id = Column(UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False)
    invitee_email = Column(Text, nullable=False)
    relation_type = Column(relation_type_enum,nullable=False)
    token = Column(Text, unique=True, nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True),nullable=False)
    used_at = Column(TIMESTAMP(timezone=True),nullable=True)
    created_at = Column(TIMESTAMP(timezone=True),server_default=text("now()"),nullable=False)
    # relationships
    patient = relationship("Patient",back_populates="share_tokens")
    inviter = relationship("User",back_populates="sent_share_tokens",foreign_keys=[inviter_user_id])
