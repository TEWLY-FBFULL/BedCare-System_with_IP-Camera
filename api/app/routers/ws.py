from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
import json
from app.websocket.manager import ws_manager
from app.core.database import get_db
from app.core.security import decode_access_token
from app.services.permission import can_read_room_patient_context
from app.models.user import User

router = APIRouter(prefix="/ws")

@router.websocket("/rooms/{room_id}")
async def websocket_room(
    websocket: WebSocket, 
    room_id: int, 
    db: Session = Depends(get_db)
):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        user = db.query(User).filter(User.user_id == user_id).first()
        
        if not user or not user.is_active or not can_read_room_patient_context(db, user=user, room_id=room_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        if payload.get("tv") != user.token_version:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept() 
        print(f"WS SUCCESS: User {user_id} connected to Room {room_id}")
        
        await ws_manager.connect(room_id, websocket)
        
        # 3. Message Loop
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)
            action = data.get("action")
            if action == "subscribe_video":
                ws_manager.set_video_subscription(room_id, websocket, True)
            elif action == "unsubscribe_video":
                ws_manager.set_video_subscription(room_id, websocket, False)

    except WebSocketDisconnect:
        ws_manager.disconnect(room_id, websocket)
    except Exception as e:
        print(f"WS UNKNOWN ERROR: {e}")
        ws_manager.disconnect(room_id, websocket)