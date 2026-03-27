from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.room_assignment import RoomAssignment
from app.models.sleep_session import SleepSession
from app.models.sleep_metric_log import SleepMetricLog
from app.models.sleep_posture_log import SleepPostureLog
from app.models.room_runtime_status import RoomRuntimeStatus
from app.services.alert_service import AlertService
from app.websocket.manager import ws_manager
from app.core.event_loop import get_event_loop
from collections import Counter
import asyncio
import numpy as np

class SleepService:
    @staticmethod
    def save(room_id, data):
        db: Session = SessionLocal()
        try:
            runtime = db.query(RoomRuntimeStatus).filter(
                RoomRuntimeStatus.room_id == room_id
            ).first()
            if not runtime: return
            assignment = (
                db.query(RoomAssignment)
                .filter(
                    RoomAssignment.room_id == room_id,
                    RoomAssignment.discharged_at.is_(None)
                )
                .first()
            )
            patient_id = assignment.patient_id if assignment else None
            session = db.query(SleepSession).filter(
                SleepSession.room_id == room_id,
                SleepSession.status == "active"
            ).first()
            if not session:
                session = SleepSession(
                    patient_id=patient_id,
                    room_id=room_id,
                    start_time=datetime.now(timezone.utc)
                )
                db.add(session)
                db.commit()
                db.refresh(session)
            posture_frames = data["posture"]
            metric_frames = data["metrics"]
            if not posture_frames or not metric_frames:
                return
            # --------- posture ---------
            posture_list = [f["label"] for f in posture_frames]
            conf_list = [f.get("confidence", 0) for f in posture_frames]
            quality_list = [f["quality"] for f in posture_frames]
            
            most_common_posture = Counter(posture_list).most_common(1)[0][0]
            avg_conf = np.mean([c for l, c in zip(posture_list, conf_list) if l == most_common_posture])
            most_common_quality = Counter([q for l, q in zip(posture_list, quality_list) if l == most_common_posture]).most_common(1)[0][0]

            posture_log = SleepPostureLog(
                session_id=session.session_id,
                patient_id=patient_id,
                posture_label=most_common_posture, 
                confidence=float(avg_conf),  
                captured_at=datetime.now(timezone.utc)
            )
            db.add(posture_log)
            # -------- metric aggregation --------
            metrics_keys = set().union(*(m.keys() for m in metric_frames))
            aggregated = {}
            for k in metrics_keys:
                values = [m[k] for m in metric_frames if k in m]
                if not values: continue
                aggregated[f"{k}_avg"] = float(np.mean(values))
                aggregated[f"{k}_max"] = float(np.max(values))
            scores = [m.get("score", 0) for m in metric_frames]
            avg_score = float(np.mean(scores)) if len(scores) > 0 else 0.0
            allowed_columns = SleepMetricLog.__table__.columns.keys()
            safe_aggregated = {k: v for k, v in aggregated.items() if k in allowed_columns}

            metric_log = SleepMetricLog(
                session_id=session.session_id,
                patient_id=patient_id,
                posture_quality=most_common_quality,
                posture_score_avg=avg_score,
                captured_at=datetime.now(timezone.utc),
                risk_flag=(avg_score < 45),
                **safe_aggregated
            )
            db.add(metric_log)
            #-------- update runtime --------
            runtime.last_ai_run = datetime.now(timezone.utc)
            runtime.updated_at = datetime.now(timezone.utc)
            db.commit()
            print(f"Saved sleep data for room {room_id} at {metric_log.captured_at.isoformat()}")
            # -------- alert --------
            AlertService.check_sleep(
                db=db,
                patient_id=patient_id,
                room_id=room_id,
                session_id=session.session_id,
                posture=most_common_posture,
                metrics=safe_aggregated,
                score=avg_score,
                quality=most_common_quality
            )
        finally:
            db.close()
        # WEBSOCKET BROADCAST
        loop = get_event_loop()
        if loop:
            # Posture
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast_room(room_id, {
                    "type": "sleep_posture",
                    "data": {
                        "label": most_common_posture,
                        "confidence": float(avg_conf),
                        "quality": most_common_quality,
                        "captured_at": posture_log.captured_at.isoformat()
                    }
                }), loop)

            # Metric
            asyncio.run_coroutine_threadsafe(
                ws_manager.broadcast_room(room_id, {
                    "type": "sleep_metric",
                    "data": {
                        "score": avg_score,
                        "quality": most_common_quality,
                        "metrics": safe_aggregated,
                        "captured_at": metric_log.captured_at.isoformat()
                    }
                }), loop)