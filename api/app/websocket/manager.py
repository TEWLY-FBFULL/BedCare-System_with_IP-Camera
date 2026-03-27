from fastapi import WebSocket
import base64

class WebSocketManager:
    def __init__(self):
        self.rooms: dict[int, list[WebSocket]] = {}
        self.video_subscribers: dict[int, set[WebSocket]] = {}

    async def connect(self, room_id: int, websocket: WebSocket):
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        self.rooms[room_id].append(websocket)

    def disconnect(self, room_id: int, websocket: WebSocket):
        if room_id in self.rooms:
            if websocket in self.rooms[room_id]:
                self.rooms[room_id].remove(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
        
        if room_id in self.video_subscribers:
            self.video_subscribers[room_id].discard(websocket)

    async def broadcast_room(self, room_id: int, data: dict):
        if room_id not in self.rooms:
            return
        dead = []
        for ws in self.rooms[room_id]:
            try:
                await ws.send_json(data)
            except:
                dead.append(ws)
        for ws in dead:
            self.disconnect(room_id, ws)

    async def broadcast_video(self, room_id: int, frame_bytes: bytes):
        if room_id not in self.video_subscribers or not self.video_subscribers[room_id]:
            return
        data = {
            "type": "video_feed",
            "frame": base64.b64encode(frame_bytes).decode('utf-8')
        }
        dead = set()
        for ws in self.video_subscribers[room_id]:
            try:
                await ws.send_json(data)
            except:
                dead.add(ws)
        
        for ws in dead:
            self.video_subscribers[room_id].discard(ws)

    def set_video_subscription(self, room_id: int, websocket: WebSocket, active: bool):
        if room_id not in self.video_subscribers:
            self.video_subscribers[room_id] = set()
        if active:
            self.video_subscribers[room_id].add(websocket)
        else:
            self.video_subscribers[room_id].discard(websocket)

ws_manager = WebSocketManager()