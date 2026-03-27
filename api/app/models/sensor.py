from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.enum import SensorTypeEnum
from app.core.database import Base

class Sensor(Base):
    __tablename__ = "sensors"
    sensor_id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.device_id", ondelete="CASCADE"), nullable=False)
    sensor_type = Column(SensorTypeEnum, nullable=False)
    # relationships
    device = relationship("Device", back_populates="sensors")