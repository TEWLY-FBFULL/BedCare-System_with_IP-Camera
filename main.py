import time
import json
import threading
import requests
import random
import os
import sys
# ==============================
# CONFIG (จำลอง)
# ==============================
API_LOGIN_URL = "https://example.com/api/device/login"
MQTT_BROKER = "broker.example.com"
running = False
shutdown_requested = False
restart_requested = False
alert_message = None
# ==============================
# MOCK SENSOR FUNCTIONS
# ==============================
def get_data_from_bme680():
    """อ่านค่า BME680"""
    return {
        "temperature_c": round(random.uniform(25, 30), 2),
        "humidity_pct": round(random.uniform(40, 60), 2),
        "pressure_hpa": round(random.uniform(1000, 1015), 2),
        "altitude_m": round(random.uniform(5, 10), 2),
    }
def get_data_from_bh1750():
    """อ่านค่าแสง"""
    return {
        "lux": round(random.uniform(100, 500), 2)
    }
def get_camera_motion():
    """จำลองสถานะกล้อง"""
    return random.choice(["no_person", "person_static", "person_moving"])
def get_radar_motion():
    """จำลองสถานะเรดาร์"""
    return random.choice(["no_person", "person_static", "person_moving"])
def get_microphone_status():
    """จำลองตรวจจับคำว่า help"""
    return random.choice([True, False])
def get_emergency_button():
    """จำลองปุ่มฉุกเฉิน"""
    return random.choice([True, False])
# ==============================
# MOCK API LOGIN
# ==============================
def login_to_server():
    """
    ยิง REST API เพื่อ login
    ได้ config กลับมา
    """
    print("🔐 Logging in to server...")
    # จำลอง response
    response = {
        "mqtt_topic": "hospital/2/environment",
        "env_log_interval_sec": 5,
        "alert_topic": "hospital/2/alert"
    }
    print("✅ Login success")
    return response
# ==============================
# MOCK MQTT
# ==============================
def mqtt_publish(topic, payload):
    """จำลองส่ง MQTT"""
    print(f"📤 Publish to {topic}")
    print(payload)
def mqtt_check_alert():
    """
    จำลองเช็ค alert จาก server
    ถ้ามี alert ให้คืนข้อความ
    """
    global alert_message
    # จำลอง random alert
    if random.randint(1, 50) == 25:
        alert_message = "🚨 ผู้ป่วยล้ม!"
    else:
        alert_message = None
def play_alert_sound(message):
    """แจ้งเตือนเสียงดัง"""
    print("🔊 ALERT:", message)
    # ใส่คำสั่งเล่นเสียงจริงภายหลังได้
# ==============================
# BUTTON HANDLING (SIMULATION)
# ==============================
def check_shutdown_button():
    """
    ถ้ากดค้าง 5 วิ → shutdown
    (จำลองด้วย random)
    """
    global shutdown_requested
    if random.randint(1, 500) == 10:
        shutdown_requested = True
def check_restart_button():
    """
    ถ้ากดค้าง 5 วิ → restart
    """
    global restart_requested
    if random.randint(1, 500) == 20:
        restart_requested = True
# ==============================
# MAIN PROGRAM
# ==============================
def main():
    global running
    global shutdown_requested
    global restart_requested
    print("🔘 กดปุ่ม START เพื่อเริ่มทำงาน...")
    time.sleep(2)  # จำลองกดปุ่ม
    # 1️⃣ Login
    config = login_to_server()
    mqtt_topic = config["mqtt_topic"]
    interval = config["env_log_interval_sec"]
    running = True
    print("🚀 Device started")
    # 2️⃣ LOOP หลัก
    while running:
        # -------------------------
        #  INTERRUPT CHECK
        # -------------------------
        check_shutdown_button()
        check_restart_button()
        mqtt_check_alert()
        if shutdown_requested:
            print("🛑 Shutdown requested")
            os.system("sudo shutdown now")
            break
        if restart_requested:
            print("🔄 Restart requested")
            os.system("sudo reboot")
            break
        if alert_message:
            play_alert_sound(alert_message)
        # -------------------------
        #  READ ALL SENSORS
        # -------------------------
        bme_data = get_data_from_bme680()
        lux_data = get_data_from_bh1750()
        payload = {
            **bme_data,
            **lux_data,
            "camera_motion_state": get_camera_motion(),
            "radar_motion_state": get_radar_motion(),
            "help_voice_detected": get_microphone_status(),
            "emergency_button_pressed": get_emergency_button(),
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        json_payload = json.dumps(payload)
        # -------------------------
        #  SEND MQTT
        # -------------------------
        mqtt_publish(mqtt_topic, json_payload)
        # -------------------------
        #  WAIT INTERVAL
        # -------------------------
        time.sleep(interval)
if __name__ == "__main__":
    main()