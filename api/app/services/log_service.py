from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from app.models.sleep_posture_log import SleepPostureLog
from app.models.sleep_metric_log import SleepMetricLog
from app.models.environment_log import EnvironmentLog
from app.models.alert_log import AlertLog
from app.models.user import User
from app.models.sleep_session import SleepSession
from app.schemas.log.response import (
    PostureLogOut,MetricLogOut,EnvironmentLogOut,AlertLogOut
)
from app.services.permission import can_read_room_patient_context
from app.utils.safe_round import safe_round

class LogService:
    @staticmethod
    def _validate_days(days: int):
        if days < 1 or days > 30:
            raise HTTPException(400, "days ต้องอยู่ระหว่าง 1-30")

    @staticmethod
    def get_posture_logs(db: Session, *, user: User, room_id: int, days: int):
        LogService._validate_days(days)
        if not can_read_room_patient_context(
            db,
            user=user,
            room_id=room_id
        ):raise HTTPException(403, "ไม่มีสิทธิ์เข้าถึงข้อมูล")
        since = datetime.now(timezone.utc) - timedelta(days=days)
        posture_logs =(
            db.query(SleepPostureLog)
            .join(SleepPostureLog.session)
            .filter(
                SleepPostureLog.captured_at >= since,
                SleepPostureLog.session.has(room_id=room_id)
            )
            .order_by(SleepPostureLog.captured_at.desc())
            .all()
        )
        return [PostureLogOut.from_orm(p) for p in posture_logs]
    
    @staticmethod
    def get_metric_logs(db: Session, *, user: User, room_id: int, days: int):
        LogService._validate_days(days)
        if not can_read_room_patient_context(
            db,
            user=user,
            room_id=room_id
        ):raise HTTPException(403, "ไม่มีสิทธิ์เข้าถึงข้อมูล")
        since = datetime.now(timezone.utc) - timedelta(days=days)
        metric_logs = (
            db.query(SleepMetricLog)
            .join(SleepSession, SleepMetricLog.session_id == SleepSession.session_id)
            .filter(
                SleepSession.room_id == room_id,
                SleepMetricLog.captured_at >= since
            )
            .order_by(SleepMetricLog.captured_at.desc())
            .all()
        )
        return [MetricLogOut.from_orm(m) for m in metric_logs]

    @staticmethod
    def get_environment_logs(db: Session, *, user: User, room_id: int, days: int):
        LogService._validate_days(days)
        if not can_read_room_patient_context(
            db,
            user=user,
            room_id=room_id
        ):raise HTTPException(403, "ไม่มีสิทธิ์เข้าถึงข้อมูล")
        since = datetime.now(timezone.utc) - timedelta(days=days)
        environment_logs = (
            db.query(EnvironmentLog)
            .filter(
                EnvironmentLog.room_id == room_id,
                EnvironmentLog.captured_at >= since
            )
            .order_by(EnvironmentLog.captured_at.desc())
            .all()
        )
        return [EnvironmentLogOut.from_orm(e) for e in environment_logs]

    @staticmethod
    def get_alert_logs(db: Session, *, user: User, room_id: int, days: int):
        LogService._validate_days(days)
        if not can_read_room_patient_context(
            db,
            user=user,
            room_id=room_id
        ):raise HTTPException(403, "ไม่มีสิทธิ์เข้าถึงข้อมูล")
        since = datetime.now(timezone.utc) - timedelta(days=days)
        alert_logs = (
            db.query(AlertLog)
            .filter(
                AlertLog.room_id == room_id,
                AlertLog.created_at >= since
            )
            .order_by(AlertLog.created_at.desc())
            .all()
        )
        return [AlertLogOut.from_orm(a) for a in alert_logs]
    
    @staticmethod
    def get_summary(db: Session, *, user: User, room_id: int, days: int):
        LogService._validate_days(days)
        if not can_read_room_patient_context(
            db, user=user, room_id=room_id
        ): raise HTTPException(403, "ไม่มีสิทธิ์เข้าถึงข้อมูล")
        since = datetime.now(timezone.utc) - timedelta(days=days)
        # ---------- 1. Sleep Posture Summary ----------
        posture_query = (
            db.query(SleepPostureLog)
            .join(SleepSession, SleepPostureLog.session_id == SleepSession.session_id)
            .filter(
                SleepSession.room_id == room_id,
                SleepPostureLog.captured_at >= since
            )
        )
        total_sessions = posture_query.with_entities(
            func.count(func.distinct(SleepPostureLog.session_id))
        ).scalar() or 0
        avg_sleep_score = posture_query.with_entities(
            func.avg(SleepPostureLog.confidence)
        ).scalar()
        dominant_posture = (
            posture_query.with_entities(
                SleepPostureLog.posture_label,
                func.count(SleepPostureLog.posture_label)
            )
            .group_by(SleepPostureLog.posture_label)
            .order_by(func.count(SleepPostureLog.posture_label).desc())
            .first()
        )
        avg_posture_label = dominant_posture[0] if dominant_posture else None
        # ---------- 2. Sleep Metric Summary ----------
        metric_query = (
            db.query(SleepMetricLog)
            .join(SleepSession, SleepMetricLog.session_id == SleepSession.session_id)
            .filter(
                SleepSession.room_id == room_id,
                SleepMetricLog.captured_at >= since
            )
        )
        avg_posture_score = metric_query.with_entities(
            func.avg(SleepMetricLog.posture_score_avg)
        ).scalar()
        risk_count = metric_query.filter(
            SleepMetricLog.risk_flag.is_(True)
        ).count()
        dominant_quality = (
            metric_query.with_entities(
                SleepMetricLog.posture_quality,
                func.count(SleepMetricLog.posture_quality)
            )
            .group_by(SleepMetricLog.posture_quality)
            .order_by(func.count(SleepMetricLog.posture_quality).desc())
            .first()
        )
        avg_posture_quality = dominant_quality[0] if dominant_quality else None
        # ---------- 3. Environment Summary ----------
        env_query = (
            db.query(EnvironmentLog)
            .filter(
                EnvironmentLog.room_id == room_id,
                EnvironmentLog.captured_at >= since
            )
        )
        env_stats = env_query.with_entities(
            func.avg(EnvironmentLog.temperature_c).label('avg_temp'),
            func.avg(EnvironmentLog.humidity_pct).label('avg_hum'),
            func.avg(EnvironmentLog.pressure_hpa).label('avg_press'),
            func.avg(EnvironmentLog.altitude_m).label('avg_alt'),
            func.avg(EnvironmentLog.lux).label('avg_lux'),
            # count motion and help events
            func.count(EnvironmentLog.env_log_id).filter(EnvironmentLog.camera_motion_state.is_(True)).label('camera_motion_count'),
            func.count(EnvironmentLog.env_log_id).filter(EnvironmentLog.radar_motion_state.is_(True)).label('radar_motion_count'),
            func.count(EnvironmentLog.env_log_id).filter(EnvironmentLog.help_voice_detected.is_(True)).label('voice_help_count'),
            func.count(EnvironmentLog.env_log_id).filter(EnvironmentLog.emergency_button_pressed.is_(True)).label('emergency_press_count')
        ).first()
        # ---------- 4. Alert Summary ----------
        alert_query = (
            db.query(AlertLog)
            .filter(
                AlertLog.room_id == room_id,
                AlertLog.created_at >= since
            )
        )
        total_alerts = alert_query.count()
        severity_counts = (
            alert_query.with_entities(
                AlertLog.severity,
                func.count(AlertLog.severity)
            )
            .group_by(AlertLog.severity)
            .all()
        )
        alerts_by_severity = {str(sev): count for sev, count in severity_counts}
        return {
            "total_sessions": total_sessions,
            "avg_sleep_score": safe_round(avg_sleep_score),
            "avg_posture_label": avg_posture_label,
            "avg_posture_quality": avg_posture_quality,
            "avg_posture_score": safe_round(avg_posture_score),
            "risk_count": risk_count,
            "avg_temperature": safe_round(env_stats.avg_temp) if env_stats else None,
            "avg_humidity": safe_round(env_stats.avg_hum) if env_stats else None,
            "avg_pressure": safe_round(env_stats.avg_press) if env_stats else None,
            "avg_altitude": safe_round(env_stats.avg_alt) if env_stats else None,
            "avg_lux": safe_round(env_stats.avg_lux) if env_stats else None,
            "camera_motion_events": env_stats.camera_motion_count if env_stats else 0,
            "radar_motion_events": env_stats.radar_motion_count if env_stats else 0,
            "voice_help_events": env_stats.voice_help_count if env_stats else 0,
            "emergency_press_events": env_stats.emergency_press_count if env_stats else 0,
            "total_alerts": total_alerts,
            "alerts_by_severity": alerts_by_severity
        }