from datetime import datetime, timezone
from sqlalchemy.orm import Session
import asyncio
from app.core.event_loop import get_event_loop
from app.models.environment_log import EnvironmentLog
from app.models.room_runtime_status import RoomRuntimeStatus
from app.models.device import Device
from app.services.alert_service import AlertService
from app.websocket.manager import ws_manager

class EnvironmentService:

    @staticmethod
    def process(db: Session, *, topic: str, payload: dict):
        parts = topic.split("/")
        if len(parts) < 3:
            return
        room_id = int(parts[1])
        device = (
            db.query(Device)
            .filter(Device.room_id == room_id)
            .first()
        )
        if not device: return
        runtime = db.query(RoomRuntimeStatus).filter(
            RoomRuntimeStatus.room_id == room_id
        ).first()
        if not runtime or not runtime.device_running:
            print(f"DEBUG: Room {room_id} runtime is inactive or device_running is False")
            return
        temperature = payload.get("temperature_c")
        humidity = payload.get("humidity_pct")
        pressure = payload.get("pressure_hpa")
        altitude = payload.get("altitude_m")
        lux = payload.get("lux")

        camera_motion = payload.get("camera_motion_state")
        radar_motion = payload.get("radar_motion_state")

        help_voice = payload.get("help_voice_detected")
        emergency_btn = payload.get("emergency_button_pressed")

        received_time = datetime.fromisoformat(payload.get("captured_at"))
        if received_time.tzinfo is None:
            received_time = received_time.replace(tzinfo=timezone.utc)
        
        device.last_seen_at = received_time
        log = EnvironmentLog(
            room_id=room_id,
            device_id=device.device_id,
            temperature_c=temperature,
            humidity_pct=humidity,
            pressure_hpa=pressure,
            altitude_m=altitude,
            lux=lux,
            camera_motion_state=camera_motion,
            radar_motion_state=radar_motion,
            help_voice_detected=help_voice,
            emergency_button_pressed=emergency_btn,
            captured_at=received_time
        )
        db.add(log)
        if runtime:
            runtime.last_env_log = received_time
            runtime.updated_at = received_time
        db.commit()
        
        print(f"Received environment data for room {room_id} at {received_time.isoformat()}")
        # ALERT ENGINE
        AlertService.check_environment(
            db=db,
            room_id=room_id,
            temperature=temperature,
            humidity=humidity,
            camera_motion=camera_motion,
            radar_motion=radar_motion,
            emergency_btn=emergency_btn
        )
        # WEBSOCKET BROADCAST
        loop = get_event_loop()
        if loop:
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast_room(
                    room_id,
                    {
                        "type": "environment",
                        "temperature_c": temperature,
                        "humidity_pct": humidity,
                        "pressure_hpa": pressure,
                        "altitude_m": altitude,
                        "lux": lux,
                        "motion_camera": camera_motion,
                        "motion_radar": radar_motion,
                        "help_voice_detected": help_voice,
                        "emergency_button": emergency_btn,
                        "captured_at": received_time.isoformat()
                    }
                ),
                loop
            )
        