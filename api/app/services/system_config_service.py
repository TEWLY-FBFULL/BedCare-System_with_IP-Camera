from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.system_config import SystemConfig
from app.models.user import User
from app.services.permission import get_role_name
from app.services.config_cache import ConfigCache
from app.schemas.admin.base import SystemConfigOut

class SystemConfigService:

    @staticmethod
    def _ensure_admin(db: Session, user: User):
        if get_role_name(db, user) != "admin":
            raise HTTPException(403, "เฉพาะ admin เท่านั้น")

    @staticmethod
    def get_all(db: Session, *, user: User):
        SystemConfigService._ensure_admin(db, user)
        configs = db.query(SystemConfig).all()
        return [SystemConfigOut.from_orm(config) for config in configs]

    @staticmethod
    def get_one(db: Session, *, user: User, key: str):
        SystemConfigService._ensure_admin(db, user)
        config = db.query(SystemConfig).filter(
            SystemConfig.config_key == key
        ).first()
        if not config:
            raise HTTPException(404, "ไม่พบ config")
        return SystemConfigOut.from_orm(config)

    @staticmethod
    def update(db: Session, *, user: User, key: str, payload):
        SystemConfigService._ensure_admin(db, user)
        config = db.query(SystemConfig).filter(
            SystemConfig.config_key == key
        ).first()
        if not config:
            raise HTTPException(404, "ไม่พบ config")
        # validate numberic
        try:
            value = int(payload.config_value)
        except (ValueError, TypeError):
            raise HTTPException(400, "config_value ต้องเป็นตัวเลข")
        if value <= 0:
            raise HTTPException(400, "config_value ต้องมากกว่า 0")
        config.config_value = value
        db.commit()
        db.refresh(config)
        ConfigCache.refresh(db)
        return SystemConfigOut.from_orm(config)