from datetime import datetime, timedelta, timezone
from app.models.sleep_posture_log import SleepPostureLog
import uuid

def test_trigger_posture_alert(db, room_id, patient_id, session_id):
    print("🚀 Simulating 3.5 hours of Supine posture...")
    now = datetime.now(timezone.utc)
    for i in range(42): 
        past_time = now - timedelta(minutes=i * 5)
        log = SleepPostureLog(
            session_id=uuid.UUID(session_id),
            patient_id=uuid.UUID(patient_id),
            posture_label="Supine",
            confidence=0.7,
            captured_at=past_time
        )
        db.add(log)
    
    db.commit()
    
    from app.services.alert_service import AlertService
    AlertService.check_sleep(
        db=db,
        patient_id=uuid.UUID(patient_id),
        room_id=room_id,
        session_id=uuid.UUID(session_id),
        posture="Supine",
        metrics={},
        score=70,
        quality="good"
    )
    print("✅ Alert check triggered. Please check 'alerts' table.")