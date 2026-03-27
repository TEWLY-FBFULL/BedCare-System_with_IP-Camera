from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.enum import relation_type_enum
from app.core.database import Base

class UserPatient(Base):
    __tablename__ = "user_patient"
    __table_args__ = (
        UniqueConstraint("user_id", "patient_id", name="uq_user_patient"),
    )
    uspa_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(relation_type_enum, nullable=False)
    # relationships
    user = relationship("User", back_populates="patient_links")
    patient = relationship("Patient", back_populates="user_links")
