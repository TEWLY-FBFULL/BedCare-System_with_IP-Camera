import time
import os
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.camera import Camera
from app.models.camera_brand import CameraBrand
from app.models.room_runtime_status import RoomRuntimeStatus
from app.services.camera_service import CameraService
from app.utils.rtspurl_generator import generate_rtsp_url
from app.utils.password import decrypt_password
import cv2
import asyncio
from app.websocket.manager import ws_manager 

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

class CameraWorker:
    def __init__(self, room_id, loop=None):
        self.room_id = room_id
        self._running = True
        self.loop = loop

    def stop(self):
        self._running = False

    def run(self):
        try:
            with SessionLocal() as db:
                camera = db.query(Camera).filter(Camera.room_id == self.room_id).first()
                rtsp_pattern = db.query(CameraBrand).filter(
                    CameraBrand.brand_id == camera.brand_id
                ).first().rtsp_pattern
                if not camera or not rtsp_pattern: 
                    print(f"Camera not found for room {self.room_id}")
                    return
                rtsp = generate_rtsp_url(
                    rtsp_pattern, 
                    camera.ip_address, 
                    camera.username, 
                    decrypt_password(camera.password))
        except Exception as e:
            print(f"Error initializing camera {self.room_id}: {e}")
            return
        
        cap = cv2.VideoCapture(rtsp, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        frame_count = 0
        last_db_check = 0
        while self._running:
            ret, frame = cap.read()
            if not ret:
                if not self._running: break
                print(f"RTSP Stream lost, retrying... room {self.room_id}")
                cap.release()
                for _ in range(5):
                    if not self._running: break
                    time.sleep(1)
                if not self._running: break
                cap.open(rtsp)
                continue

            small_frame = cv2.resize(frame, (640, 640))    
            frame_count += 1

            if frame_count % 10 == 0:
                _, buffer = cv2.imencode('.jpg', small_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if self.loop and self.loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        ws_manager.broadcast_video(self.room_id, buffer.tobytes()),
                        self.loop
                    )
                else:
                    print("Warning: Main loop is not running yet.")

            if frame_count % 15 == 0:
                try:
                    CameraService.process_frame(room_id=self.room_id, frame=small_frame)
                except Exception as e:
                    print(f"⚠️ AI Skip: {e}")
            
            if time.time() - last_db_check > 5:
                try:
                    with SessionLocal() as db:
                        runtime = db.query(RoomRuntimeStatus).filter(
                            RoomRuntimeStatus.room_id == self.room_id
                        ).first()
                    
                        if not runtime or not runtime.camera_running:
                            self._running = False
                            break
                        
                        runtime.last_ai_run = datetime.now(timezone.utc)
                        runtime.updated_at = datetime.now(timezone.utc)
                        db.commit()
                    last_db_check = time.time()      
                except Exception as e:
                    print(f"Database error in CameraWorker room {self.room_id}: {e}")
                    time.sleep(1)
            time.sleep(0.01)
        cap.release()
        print(f"CameraWorker stopped for room {self.room_id}")