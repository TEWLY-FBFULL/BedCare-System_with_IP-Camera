from datetime import datetime, timedelta, timezone
from app.models.sleep_metric_log import SleepMetricLog
import uuid

def test_metric_alerts(db, room_id, patient_id, session_id):
    s_id = uuid.UUID(session_id)
    p_id = uuid.UUID(patient_id)
    now = datetime.now(timezone.utc)
    print("🚨 Simulating 1 hour of 'danger' quality...")
    # สร้าง Metric Log ย้อนหลัง 12 แถว (12 * 5 นาที = 60 นาที)
    for i in range(12):
        past_time = now - timedelta(minutes=i * 5)
        metric_log = SleepMetricLog(
            session_id=s_id,
            patient_id=p_id,
            posture_quality="danger",
            posture_score_avg=30.0,
            risk_flag=True,
            captured_at=past_time
        )
        db.add(metric_log)
    db.commit()

    from app.services.alert_service import AlertService
    print("--- Testing Emergency Metric ---")
    AlertService.check_sleep(
        db=db, patient_id=p_id, room_id=room_id, session_id=s_id,
        posture="To-Left", metrics={}, score=30, quality="danger"
    )

    print("\n⚠️ Testing Warning Metric (Poor quality)...")
    AlertService.check_sleep(
        db=db, patient_id=p_id, room_id=room_id, session_id=s_id,
        posture="To-Left", metrics={}, score=45, quality="poor"
    )