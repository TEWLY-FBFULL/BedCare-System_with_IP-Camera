from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone, timedelta
import json
from app.models.alert_log import AlertLog
from app.models.room import Room
from app.models.room_assignment import RoomAssignment
from app.models.sleep_posture_log import SleepPostureLog
from app.models.sleep_metric_log import SleepMetricLog
from app.models.enum import AlertTypeEnumClass, SeverityEnumClass
from app.services.config_cache import ConfigCache
from app.services.email_service import EmailService
from app.services.telegram_service import TelegramVoiceService
import asyncio
from app.core.event_loop import get_event_loop
from app.websocket.manager import ws_manager
import os

class AlertService:

    @staticmethod
    def check_environment(
        db: Session,
        *,
        room_id: int,
        temperature: float | None,
        humidity: float | None,
        camera_motion: bool | None,
        radar_motion: bool | None,
        emergency_btn: bool | None
    ):
        try:
            min_temp = float(ConfigCache.get("min_temperature_c"))
            max_temp = float(ConfigCache.get("max_temperature_c"))
            min_humidity = float(ConfigCache.get("min_humidity_pct"))
            max_humidity = float(ConfigCache.get("max_humidity_pct"))
        except Exception as e:
            print(f"DEBUG: Config Error: {e}")
            return
        print(f"DEBUG: Checking room {room_id} | Temp: {temperature} (Range: {min_temp}-{max_temp}) | Hum: {humidity} (Range: {min_humidity}-{max_humidity})")

        assignment = (
            db.query(RoomAssignment)
            .filter(
                RoomAssignment.room_id == room_id,
                RoomAssignment.discharged_at.is_(None)
            )
            .first()
        )
        patient_id = assignment.patient_id if assignment else None

        # -------- EMERGENCY --------
        if emergency_btn or (not camera_motion and not radar_motion):
            AlertService.try_create_alert(
                db=db,
                room_id=room_id,
                alert_type=AlertTypeEnumClass.environment,
                patient_id=patient_id,
                severity=SeverityEnumClass.emergency,
                source="device",
                value="emergency",
                message="ตรวจพบเหตุฉุกเฉินจากอุปกรณ์"
            )
        # -------- WARNING --------
        if temperature is not None and (temperature < min_temp or temperature > max_temp):
            AlertService.try_create_alert(
                db=db,
                room_id=room_id,
                alert_type=AlertTypeEnumClass.environment,
                patient_id=patient_id,
                severity=SeverityEnumClass.warning,
                source="sensor",
                value=str(temperature),
                message="อุณหภูมิไม่เหมาะสม"
            )
        if humidity is not None and (humidity < min_humidity or humidity > max_humidity):
            AlertService.try_create_alert(
                db=db,
                room_id=room_id,
                alert_type=AlertTypeEnumClass.environment,
                patient_id=patient_id,
                severity=SeverityEnumClass.warning,
                source="sensor",
                value=str(humidity),
                message="ความชื้นไม่เหมาะสม"
            )

    @staticmethod
    def _get_interval_minutes():
        interval_sec = int(ConfigCache.get("sleep_log_interval_sec", 300))
        return interval_sec / 60

    @staticmethod
    def _calculate_posture_duration(logs, current_posture):
        if not logs: return 0
        interval_min = AlertService._get_interval_minutes()
        total_minutes = 0
        for i in range(len(logs)):
            if logs[i].posture_label != current_posture:
                print(f"DEBUG: Stopped counting because posture changed to {logs[i].posture_label}")
                break
            if i > 0:
                diff = (logs[i-1].captured_at - logs[i].captured_at).total_seconds() / 60
                if diff > (interval_min * 2.1): 
                    print(f"DEBUG: Stopped counting due to time gap: {diff:.2f} min")
                    break
            total_minutes += interval_min   
        return total_minutes / 60
    
    @staticmethod
    def _check_metric_duration(db, session_id, target_quality, hours):
        interval_min = AlertService._get_interval_minutes()
        num_logs = int((hours * 60) / interval_min)
        recent_logs = db.query(SleepMetricLog.posture_quality).filter(
            SleepMetricLog.session_id == session_id
        ).order_by(SleepMetricLog.captured_at.desc()).limit(num_logs).all()
        if len(recent_logs) < num_logs:
            return False
        return all(log.posture_quality == target_quality for log in recent_logs)

    @staticmethod
    def check_sleep(db, *, patient_id, room_id, session_id, posture, metrics, score, quality):
        now = datetime.now(timezone.utc)
        # Check Posture Duration Alert
        # Query in 3 hours window
        cutoff_time = now - timedelta(hours=3)
        recent_logs = db.query(SleepPostureLog).filter(
            SleepPostureLog.session_id == session_id,
            SleepPostureLog.captured_at >= cutoff_time
        ).order_by(SleepPostureLog.captured_at.desc()).all()

        # --------- Posture Alert (Quality-based) ---------
        duration_hours = AlertService._calculate_posture_duration(recent_logs, posture)
        print(f"DEBUG: Recent logs found: {len(recent_logs)}") # เช็คว่าเจอ Log ไหม
        print(f"DEBUG: Calculated duration for {posture}: {duration_hours} hours")
        # Emergency (3 hours ++)
        if duration_hours >= 3:
            AlertService.try_create_alert(
                db, 
                room_id=room_id, 
                alert_type=AlertTypeEnumClass.posture, 
                patient_id=patient_id, 
                severity=SeverityEnumClass.emergency, 
                source="ai", 
                value=str(duration_hours), 
                message=f"ผู้ป่วยอยู่ในท่าเดิมติดต่อกันนานเกินไป ({duration_hours:.1f} ชม.)"
            )
        # Warning (2 hours ++)
        elif duration_hours >= 2:
            AlertService.try_create_alert(
                db, 
                room_id=room_id, 
                alert_type=AlertTypeEnumClass.posture, 
                patient_id=patient_id, 
                severity=SeverityEnumClass.warning, 
                source="ai", 
                value=str(duration_hours), 
                message=f"แนะนำเปลี่ยนท่าทางการนอน"
            )

        # --------- Metric Alert (Quality-based) ---------

        # Emergency (1 hours ++)
        if quality == 'danger': 
            if AlertService._check_metric_duration(db, session_id, 'danger', 1):
                AlertService.try_create_alert(
                    db, 
                    room_id=room_id, 
                    alert_type=AlertTypeEnumClass.posture, 
                    patient_id=patient_id, 
                    severity=SeverityEnumClass.emergency, 
                    source="ai", 
                    value="danger", 
                    message="คุณภาพท่าทางการนอนวิกฤตสำหรับ 1 ชั่วโมง"
                )
        # Warning
        elif quality == 'poor' or score <= 45: 
            AlertService.try_create_alert(
                db, 
                room_id=room_id, 
                alert_type=AlertTypeEnumClass.posture, 
                patient_id=patient_id, 
                severity=SeverityEnumClass.warning, 
                source="ai", 
                value=quality, 
                message="คุณภาพท่าทางการนอนไม่ดี แนะนำให้เปลี่ยนท่าทางการนอน"
            )

    @staticmethod
    def try_create_alert(
        db: Session,
        *,
        room_id,
        alert_type,
        patient_id,
        severity,
        source,
        value,
        message
    ):
        now = datetime.now(timezone.utc)
        if severity == SeverityEnumClass.warning:
            try:
                cooldown = int(ConfigCache.get("warning_alert_cooldown_sec"))
            except (ValueError, TypeError):
                cooldown = 900  # Default to 15 minutes
        else:
            try:
                cooldown = int(ConfigCache.get("emergency_alert_cooldown_sec"))
            except (ValueError, TypeError):
                cooldown = 3600  # Default to 1 hour
        last_alert = (
            db.query(AlertLog)
            .filter(
                AlertLog.room_id == room_id,
                AlertLog.severity == severity
            )
            .order_by(AlertLog.created_at.desc())
            .first()
        )
        if last_alert:
            last_created = last_alert.created_at
            if last_created.tzinfo is None:
                last_created = last_created.replace(tzinfo=timezone.utc)
            delta = (now - last_created).total_seconds()
            if delta < cooldown:
                print(f"DEBUG: Alert suppressed by cooldown (Delta: {delta}s < {cooldown}s)")
                return # Cooldown
        alert = AlertLog(
            patient_id=patient_id,
            room_id=room_id,
            alert_type=alert_type,
            severity=severity,
            trigger_source=source,
            trigger_value=value,
            message=message,
            created_at=now
        )
        db.add(alert)
        db.commit()
        # send notification
        AlertService.dispatch(db, alert, severity)

    @staticmethod
    def dispatch(db: Session, alert: AlertLog, severity: SeverityEnumClass):
        from app.mqtt.client import get_mqtt
        mqtt_manager = get_mqtt()
        room = (
            db.query(Room)
            .options(joinedload(Room.facility))
            .filter(Room.room_id == alert.room_id)
            .first()
        )
        if severity == SeverityEnumClass.warning:
            print("WARNING ALERT:", alert.message)
            # EMAIL
            EmailService.send_alert(db, alert, room)
        elif severity == SeverityEnumClass.emergency:
            print("EMERGENCY ALERT:", alert.message)
            # TELEGRAM
            msg = f"แจ้งเหตุฉุกเฉินค่ะ {alert.message} ที่ห้อง {room.room_number} โปรดตรวจสอบด่วนค่ะ"
            TelegramVoiceService.simulate_call(msg)
            # EMAIL
            EmailService.send_alert(db, alert, room)
        # MQTT notify device
        topic_prefix = room.facility.facility_type
        topic = f"{topic_prefix}/{alert.room_id}/environment"
        mqtt_manager.client.publish(
            topic,
            json.dumps({
                "alert": True,
                "severity": severity.value,
                "message": alert.message,
            })
        )
        DEVTEST_URL = os.getenv("DEVTEST_URL")
        ack_url = f"{DEVTEST_URL}/alerts/acknowledge/{alert.alert_id}"
        # WEBSOCKET BROADCAST
        loop = get_event_loop()
        if loop:
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast_room(
                    alert.room_id,
                    {
                        "type": "alert",
                        "data": {
                            "alert_id": alert.alert_id,
                            "severity": severity.value,
                            "message": alert.message,
                            "ack_url": ack_url if severity == SeverityEnumClass.emergency else None,
                            "trigger_source": alert.trigger_source,
                            "created_at": alert.created_at.isoformat()
                        }
                    }
                ),
                loop
            )