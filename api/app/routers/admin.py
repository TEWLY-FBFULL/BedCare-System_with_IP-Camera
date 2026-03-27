from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.role_guard import get_current_active_user, require_roles
from app.models.user import User
from app.services.system_config_service import SystemConfigService
from app.schemas.admin.base import (
    SystemConfigOut,
    SystemConfigUpdate
)

router = APIRouter(prefix="/admin",tags=["Admin"])


@router.get(
    "/system-configs",
    summary="Get all system configs",
    response_model=List[SystemConfigOut],
    dependencies=[Depends(require_roles(["admin"]))]
)
def get_all_configs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return SystemConfigService.get_all(db, user=user)


@router.get(
    "/system-configs/{key}",
    summary="Get system config by key",
    response_model=SystemConfigOut,
    dependencies=[Depends(require_roles(["admin"]))]
)
def get_config(
    key: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return SystemConfigService.get_one(db, user=user, key=key)


@router.patch(
    "/system-configs/{key}",
    summary="Update system config value",
    response_model=SystemConfigOut,
    dependencies=[Depends(require_roles(["admin"]))]
)
def update_config(
    key: str,
    payload: SystemConfigUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return SystemConfigService.update(db,user=user,key=key,payload=payload)