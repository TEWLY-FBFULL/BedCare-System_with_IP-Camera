from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import threading
from app.services.config_cache import ConfigCache
from app.core.database import SessionLocal
import app.models 
from app.routers import (
    auth, users, master_data, 
    patient, facility, room, 
    device, camera, log, 
    admin, ws, room_runtime,
    alert_log
)
from fastapi.openapi.docs import get_swagger_ui_html
from app.core.basic_auth_docs import verify_credentials
from app.core.scheduler import start_scheduler
from app.core.event_loop import set_event_loop
from app.mqtt.client import get_mqtt
from app.camera.camera_runtime import camera_runtime_loop

app = FastAPI( 
    title="SleepCareSystem API", 
    docs_url=None, 
    redoc_url=None, 
    openapi_url="/openapi.json",
    root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def load_config():
    # register main event loop
    loop = asyncio.get_running_loop()
    set_event_loop(loop)
    db = SessionLocal()
    start_scheduler()
    try:
        ConfigCache.refresh(db)
        print("Config loaded:", ConfigCache._cache)
    finally:
        db.close()
    # start MQTT
    mqtt = get_mqtt()
    mqtt.subscribe("+/+/environment")
    # start camera runtime loop
    threading.Thread(
        target=camera_runtime_loop,
        args=(loop,),
        daemon=True
    ).start()

@app.get("/docs", include_in_schema=False)
def custom_docs(dep: str = Depends(verify_credentials)):
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="SleepCareSystem API Docs"
    )

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(master_data.router)
app.include_router(patient.router)
app.include_router(facility.router)
app.include_router(room.router)
app.include_router(device.router)
app.include_router(camera.router)
app.include_router(log.router)
app.include_router(room_runtime.router)
app.include_router(admin.router)
app.include_router(ws.router)
app.include_router(alert_log.router)