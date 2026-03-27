from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict
from decimal import Decimal

# ---------- POSTURE ----------
class PostureLogOut(BaseModel):
    posture_label: str
    confidence: Optional[Decimal]
    captured_at: datetime
    class Config:
        orm_mode = True

# ---------- METRIC ----------
class MetricLogOut(BaseModel):
    posture_quality: Optional[str]
    posture_score_avg: Optional[Decimal]
    risk_flag: bool
    captured_at: datetime
    class Config:
        orm_mode = True

# ---------- ENV ----------
class EnvironmentLogOut(BaseModel):
    temperature_c: Optional[Decimal]
    humidity_pct: Optional[Decimal]
    pressure_hpa: Optional[Decimal]
    altitude_m: Optional[Decimal]
    lux: Optional[Decimal]
    camera_motion_state: Optional[bool]
    radar_motion_state: Optional[bool]
    help_voice_detected: Optional[bool]
    emergency_button_pressed: Optional[bool]
    captured_at: datetime
    class Config:
        orm_mode = True

# ---------- ALERT ----------
class AlertLogOut(BaseModel):
    alert_type: str
    severity: str
    message: Optional[str]
    trigger_source: Optional[str]
    trigger_value: Optional[str]
    is_acknowledged: bool
    created_at: datetime
    resolved_at: Optional[datetime]
    class Config:
        orm_mode = True

# ---------- SUMMARY ----------
class LogSummaryOut(BaseModel):
    # posture
    total_sessions: int
    avg_sleep_score: Optional[Decimal]
    avg_posture_label: Optional[str]
    # metric
    avg_posture_quality: Optional[str]
    avg_posture_score: Optional[Decimal]
    risk_count: int
    # environment
    avg_temperature: Optional[Decimal]
    avg_humidity: Optional[Decimal]
    avg_pressure: Optional[Decimal]
    avg_altitude: Optional[Decimal]
    avg_lux: Optional[Decimal]
    camera_motion_events: int
    radar_motion_events: int
    voice_help_events: int
    emergency_press_events: int
    # alerts
    total_alerts: int
    alerts_by_severity: Dict[str, int]