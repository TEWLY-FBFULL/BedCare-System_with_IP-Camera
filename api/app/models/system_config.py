from sqlalchemy import Column, String, TIMESTAMP, text
from app.core.database import Base

class SystemConfig(Base):
    __tablename__ = "system_configs"
    config_key = Column(String, primary_key=True)
    config_value = Column(String, nullable=False)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=text("now()"),
        nullable=False
    )
    description = Column(String)