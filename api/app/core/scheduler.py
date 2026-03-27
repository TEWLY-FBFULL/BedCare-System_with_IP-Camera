from apscheduler.schedulers.background import BackgroundScheduler
from app.services.device_monitor import check_device_timeout
from app.services.camera_monitor import check_camera_timeout

scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(
        check_device_timeout,
        "interval",
        seconds=30
    )
    scheduler.add_job(
        check_camera_timeout,
        "interval",
        seconds=30
    )
    scheduler.start()