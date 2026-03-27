from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.role_guard import get_current_active_user
from app.services.device_service import DeviceService
from app.schemas.device.request import DeviceCreate, DeviceUpdate, SensorCreate, DeviceLoginRequest
from app.schemas.device.response import DeviceOut, DeviceCreateOut, DeviceLoginResponse
from app.models.user import User

router = APIRouter(prefix="/rooms", tags=["Rooms Device"])


@router.get(
    "/device/sensor-types",
    summary="Get all sensor types",
    description="ดึงรายการประเภทเซนเซอร์ทั้งหมดที่รองรับในระบบ **สิทธิ์การเข้าถึง:** ทุกคนที่ล็อกอินเข้าสู่ระบบได้สามารถเข้าถึงข้อมูลนี้ได้"
)
def get_sensor_types(user:User=Depends(get_current_active_user)):
    return DeviceService.get_sensor_types_(user)


@router.get(
    "/{room_id}/device", 
    summary="Get device detail",
    description="""
    ดึงรายละเอียดอุปกรณ์ในห้องพักตามรหัสห้องพัก (room_id) ในสถานที่ดูแลที่ผู้ใช้งานสังกัดอยู่
    **สิทธิ์การเข้าถึง:**
    admin เห็นทั้งหมด ,
    ทุกคนในสถานที่ดูเเลเห็นอุปกรณ์ในห้องพักที่ตัวเองสังกัดอยู่ได้
    """,
    response_model=DeviceOut
)
def get_device(room_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_active_user)):
    return DeviceService.get(db,user=user,room_id=room_id)


@router.post(
    "/{room_id}/device",
    summary="Create device",
    description="""
    สร้างอุปกรณ์ในห้องพักตามรหัสห้องพัก (room_id) ในสถานที่ดูแลที่ผู้ใช้งานสังกัดอยู่
    หลังจากนั้นจะได้ token ของอุปกรณ์มา ซึ่งสามารถนำไปใส่ในอุปกรณ์เพื่อให้ส่งข้อมูลเข้ามาได้
    **สิทธิ์การเข้าถึง:**
    owner / manager สร้างอุปกรณ์ในห้องพักที่ตัวเองสังกัดอยู่ได้
    **Payload**
    device_name: ชื่ออุปกรณ์
    """,
    response_model=DeviceCreateOut
)
def create_device(room_id:int, payload:DeviceCreate, db:Session=Depends(get_db), user:User=Depends(get_current_active_user)):
    return DeviceService.create(db,user=user,room_id=room_id,payload=payload)


@router.post(
    "/{room_id}/device/sensors",
    summary="Create sensor in device",
    description="""
    สร้างเซ็นเซอร์ในอุปกรณ์ในห้องพักตามรหัสห้องพัก (room_id) ในสถานที่ดูแลที่ผู้ใช้งานสังกัดอยู่
    **สิทธิ์การเข้าถึง:**
    owner / manager สร้างเซ็นเซอร์ในอุปกรณ์ในห้องพักที่ตัวเองสังกัดอยู่ได้
    **Payload**
    sensor_types รายการประเภทเซ็นเซอร์ที่ต้องการเพิ่ม เช่น pi_camera_motion, bme680, bh1750, hlk_ld2410, usb_microphone, emergency_button
    """,
)
def create_sensor(
    room_id: int,
    payload: SensorCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_active_user)
):
    return DeviceService.create_sensors(db, user=user, room_id=room_id, payload=payload)


@router.patch(
    "/{room_id}/device",
    summary="Update device",
    description="""
    อัปเดตข้อมูลอุปกรณ์ในห้องพักตามรหัสห้องพัก (room_id) ในสถานที่ดูแลที่ผู้ใช้งานสังกัดอยู่
    **สิทธิ์การเข้าถึง:**
    owner / manager อัปเดตอุปกรณ์ในห้องพักที่ตัวเองสังกัดอยู่ได้
    **Payload**
    device_name: ชื่ออุปกรณ์ ไม่จำเป็น ,
    is_active: สถานะการใช้งานของอุปกรณ์ true/false ไม่จำเป็น,
    """,
)
def update_device(room_id:int, payload:DeviceUpdate, db:Session=Depends(get_db), user:User=Depends(get_current_active_user)):
    return DeviceService.update(db,user=user,room_id=room_id,payload=payload)


@router.delete(
    "/{room_id}/device",
    summary="Delete device and sensors",
    description="""
    ลบอุปกรณ์ในห้องพักเเละเซ็นเซอร์ทั้งหมดในอุปกรณ์ตามรหัสห้องพัก (room_id) ในสถานที่ดูแลที่ผู้ใช้งานสังกัดอยู่
    **สิทธิ์การเข้าถึง:**
    owner / admin เท่านั้นที่ลบอุปกรณ์ในห้องพักที่ตัวเองสังกัดอยู่ได้
    """
)
def delete_device(room_id:int, db:Session=Depends(get_db), user:User=Depends(get_current_active_user)):
    return DeviceService.delete(db,user=user,room_id=room_id)


@router.post(
    "/devices/login",
    summary="Device login and get MQTT configuration",
    description="""
    อุปกรณ์ล็อกอินเข้าสู่ระบบด้วย device_token เพื่อรับข้อมูลการเชื่ออมต่อ MQTT และข้อมูลอื่นๆ ที่จำเป็นในการส่งข้อมูลเซ็นเซอร์เข้ามา
    **สิทธิ์การเข้าถึง:**
    อุปกรณ์ที่มี device_token ถูกต้องสามารถเข้าถึงข้อมูลนี้ได้
    **Payload**
    device_token: token ของอุปกรณ์ที่ได้มาจากการสร้างอุปกรณ์
    """,
    response_model=DeviceLoginResponse
)
def device_login(payload: DeviceLoginRequest,db: Session = Depends(get_db)
):
    return DeviceService.login(db, device_token=payload.device_token)