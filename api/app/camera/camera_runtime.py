import threading
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.camera import Camera
from app.models.room_runtime_status import RoomRuntimeStatus
from app.camera.camera_worker import CameraWorker
from app.ai.aggregation import aggregation_buffers, AggregationBuffer

workers = {}

def camera_runtime_loop(main_loop):

    while True:
        db: Session = SessionLocal()
        try:
            cameras = db.query(Camera).filter(Camera.is_active == True).all()
            for cam in cameras:
                runtime = db.query(RoomRuntimeStatus).filter(
                    RoomRuntimeStatus.room_id == cam.room_id,
                    RoomRuntimeStatus.room_active == True
                ).first()
                if not runtime:
                    continue

                if runtime.camera_running and cam.room_id not in workers:
                    print(f"Start camera worker room {cam.room_id}")
                    runtime.last_ai_run = datetime.now(timezone.utc)
                    runtime.updated_at = datetime.now(timezone.utc)
                    aggregation_buffers[cam.room_id] = AggregationBuffer()
                    worker = CameraWorker(cam.room_id, main_loop)
                    t = threading.Thread(target=worker.run, daemon=True)
                    workers[cam.room_id] = {"thread": t, "worker": worker}
                    t.start()
                if not runtime.camera_running and cam.room_id in workers:
                    print(f"Stop camera worker room {cam.room_id}")
                    runtime.updated_at = datetime.now(timezone.utc)
                    worker_obj = workers[cam.room_id]['worker']
                    worker_obj.stop()
                    del workers[cam.room_id]
                    if cam.room_id in aggregation_buffers:
                        del aggregation_buffers[cam.room_id]
        finally:
            db.close()
        time.sleep(10)