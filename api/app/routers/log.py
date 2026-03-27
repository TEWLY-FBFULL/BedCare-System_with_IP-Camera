from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.role_guard import get_current_active_user
from app.models.user import User
from app.services.log_service import LogService
from app.schemas.log.response import (
    PostureLogOut,
    MetricLogOut,
    EnvironmentLogOut,
    AlertLogOut,
    LogSummaryOut
)

router = APIRouter(prefix="/rooms/{room_id}/logs", tags=["Rooms Logs"])


@router.get(
    "/posture", 
    summary="get posture logs of a room",
    description="""
    ดึงข้อมูลท่านอนย้อนหลังของผู้ป่วยในห้องตามจำนวนวันที่ระบุ
    **สิทธิ์การเข้าถึง:**
    admin เห็นข้อมูลทั้งหมด,
    owner/manager เห็นข้อมูลทั้งหมดของห้องที่ตนเองสังกัดสถานที่อยู่,
    ผู้ใช้งานทั่วไปเห็นข้อมูลได้ต้องเกี่ยวข้องกับผู้ป่วยในห้องนั้นๆ เเละต้องสังกัดอยู่ในสถานที่ดูแลเดียวกัน
    **Query Parameters:**
    - days: จำนวนวันที่ต้องการดึงข้อมูลย้อนหลัง (ค่าเริ่มต้น: 7 วัน, ตัวเลือก: 1-30 วัน)
    """,
    response_model=List[PostureLogOut])
def get_posture_logs(
    room_id: int,
    days: int = Query(7),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return LogService.get_posture_logs(db, user=user, room_id=room_id, days=days)


@router.get(
    "/metric", 
    summary="get metric logs of a room",
    description="""
    ดึงข้อมูลค่าเมทริกซ์ของท่านอนต่างๆย้อนหลังของผู้ป่วยในห้องตามจำนวนวันที่ระบุ
    **สิทธิ์การเข้าถึง:**
    admin เห็นข้อมูลทั้งหมด,
    owner/manager เห็นข้อมูลทั้งหมดของห้องที่ตนเองสังกัดสถานที่อยู่,
    ผู้ใช้งานทั่วไปเห็นข้อมูลได้ต้องเกี่ยวข้องกับผู้ป่วยในห้องนั้นๆ เเละต้องสังกัดอยู่ในสถานที่ดูแลเดียวกัน
    **Query Parameters:**
    - days: จำนวนวันที่ต้องการดึงข้อมูลย้อนหลัง (ค่าเริ่มต้น: 7 วัน, ตัวเลือก: 1-30 วัน)
    """,
    response_model=List[MetricLogOut])
def get_metric_logs(
    room_id: int,
    days: int = Query(7),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return LogService.get_metric_logs(db, user=user, room_id=room_id, days=days)


@router.get(
    "/environment", 
    summary="get environment logs of a room",
    description="""
    ดึงข้อมูลสภาพแวดล้อมย้อนหลังของผู้ป่วยในห้องตามจำนวนวันที่ระบุ
    **สิทธิ์การเข้าถึง:**
    admin เห็นข้อมูลทั้งหมด,
    owner/manager เห็นข้อมูลทั้งหมดของห้องที่ตนเองสังกัดสถานที่อยู่,
    ผู้ใช้งานทั่วไปเห็นข้อมูลได้ต้องเกี่ยวข้องกับผู้ป่วยในห้องนั้นๆ เเละต้องสังกัดอยู่ในสถานที่ดูแลเดียวกัน
    **Query Parameters:**
    - days: จำนวนวันที่ต้องการดึงข้อมูลย้อนหลัง (ค่าเริ่มต้น: 7 วัน, ตัวเลือก: 1-30 วัน)
    """,
    response_model=List[EnvironmentLogOut])
def get_environment_logs(
    room_id: int,
    days: int = Query(7),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return LogService.get_environment_logs(db, user=user, room_id=room_id, days=days)


@router.get(
    "/alerts", 
    summary="get alert logs of a room",
    description="""
    ดึงข้อมูลการแจ้งเตือนย้อนหลังของผู้ป่วยในห้องตามจำนวนวันที่ระบุ
    **สิทธิ์การเข้าถึง:**
    admin เห็นข้อมูลทั้งหมด,
    owner/manager เห็นข้อมูลทั้งหมดของห้องที่ตนเองสังกัดสถานที่อยู่,
    ผู้ใช้งานทั่วไปเห็นข้อมูลได้ต้องเกี่ยวข้องกับผู้ป่วยในห้องนั้นๆ เเละต้องสังกัดอยู่ในสถานที่ดูแลเดียวกัน
    **Query Parameters:**
    - days: จำนวนวันที่ต้องการดึงข้อมูลย้อนหลัง (ค่าเริ่มต้น: 7 วัน, ตัวเลือก: 1-30 วัน)
    """,
    response_model=List[AlertLogOut])
def get_alert_logs(
    room_id: int,
    days: int = Query(7),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return LogService.get_alert_logs(db, user=user, room_id=room_id, days=days)


@router.get(
    "/summary",
    summary="get analytics summary of a room",
    description="""
    ดึงข้อมูลสรุปเชิงวิเคราะห์ของผู้ป่วยในห้องตามจำนวนวันที่ระบุ
    **ข้อมูลที่ได้:**
    - จำนวน session
    - ค่าเฉลี่ย sleep score
    - ระยะเวลาการนอนเฉลี่ย
    - ท่านอนหลัก
    - ค่าเฉลี่ย posture score
    - จำนวน risk flag
    - ค่าเฉลี่ยอุณหภูมิ / ความชื้น / แสง
    - จำนวน alert และแยกตามระดับความรุนแรง
    **สิทธิ์การเข้าถึง:**
    admin เห็นข้อมูลทั้งหมด,
    owner/manager เห็นข้อมูลทั้งหมดของห้องที่ตนเองสังกัดสถานที่อยู่,
    ผู้ใช้งานทั่วไปเห็นข้อมูลได้ต้องเกี่ยวข้องกับผู้ป่วยในห้องนั้นๆ เเละต้องสังกัดอยู่ในสถานที่ดูแลเดียวกัน
    **Query Parameters:**
    - days: จำนวนวันที่ต้องการดึงข้อมูลย้อนหลัง (ค่าเริ่มต้น: 7 วัน, ตัวเลือก: 1-30 วัน)
    """,
    response_model=LogSummaryOut
)
def get_summary(
    room_id: int,
    days: int = Query(7),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return LogService.get_summary(db, user=user, room_id=room_id, days=days)