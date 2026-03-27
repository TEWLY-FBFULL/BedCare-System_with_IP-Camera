from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.room_runtime_status import RoomRuntimeStatus
from app.services.config_cache import ConfigCache

def check_camera_timeout():
    db: Session = SessionLocal()
    try:
        interval = int(ConfigCache.get("sleep_log_interval_sec"))
        now = datetime.now(timezone.utc)
        runtimes = db.query(RoomRuntimeStatus).filter(
            RoomRuntimeStatus.camera_running == True
        ).all()

        for r in runtimes:
            last_activity = r.last_ai_run or r.updated_at
            
            if not last_activity:
                r.camera_running = False
                continue
            # UTC Aware Datetime
            if last_activity.tzinfo is None:
                last_activity = last_activity.replace(tzinfo=timezone.utc)
            else:
                last_activity = last_activity.astimezone(timezone.utc)
            delta = (now - last_activity).total_seconds()
            
            if delta > interval * 2:
                print(f"!!! CAMERA TIMEOUT: Room {r.room_id} (Delta: {delta:.0f}s)")
                r.camera_running = False
                
        db.commit()
    except Exception as e:
        print(f"Error in check_camera_timeout: {e}")
    finally:
        db.close()