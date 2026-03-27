from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.role_guard import get_current_active_user
from app.models.user import User
from app.schemas.room_runtime.response import RoomRuntimeOut
from app.schemas.room_runtime.request import RoomRuntimeUpdate
from app.services.room_runtime_service import RoomRuntimeService

router = APIRouter(
    prefix="/rooms",
    tags=["Rooms Runtime"]
)

@router.get(
    "/{room_id}/room-runtime",
    response_model=RoomRuntimeOut,
    summary="Get room runtime status"
)
def get_room_runtime(
    room_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return RoomRuntimeService.get(db, user=user, room_id=room_id)


@router.patch(
    "/{room_id}/room-runtime",
    summary="Update room runtime status"
)
def update_room_runtime(
    room_id: int,
    payload: RoomRuntimeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return RoomRuntimeService.update(
        db,
        user=user,
        room_id=room_id,
        payload=payload
    )