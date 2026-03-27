import os
import time
import json
import requests
import threading
import tkinter as tk
from tkinter import messagebox
from dotenv import load_dotenv, set_key
import paho.mqtt.client as mqtt
# --- Import Sensor Libraries ---
from bh1750_sensor import read_light
from bme680_sensor import read_bme
from oled_display import OLED
from person_detector import PersonDetector
from ld2410_sensor import LD2410
from datetime import datetime, timezone
from gtts import gTTS
import pygame

# ==============================
# CONFIG & ENV SETUP
# ==============================
ENV_FILE = ".env"
load_dotenv(ENV_FILE)

class DeviceApp:
    def __init__(self):
        self.running = False
        self.mqtt_client = None
        self.config = {}
        
        # Initialize Sensors
        self.oled = OLED()
        self.camera_detector = PersonDetector()
        self.radar_detector = LD2410()
        
        # Internal State
        self.current_data = {}

    def speak_thai(self, text):
        def _speak():
            try:
                tts = gTTS(text=text, lang='th')
                filename = "alert.mp3"
                tts.save(filename)
                
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                pygame.mixer.music.unload()
                os.remove(filename)
            except Exception as e:
                print(f"🔊 Voice Error: {e}")
        threading.Thread(target=_speak, daemon=True).start()

    # --- 1. GUI Setup ---
    def show_setup_gui(self):
        root = tk.Tk()
        root.title("SleepCare Device Setup")
        root.geometry("400x350")
        root.eval('tk::PlaceWindow . center')

        tk.Label(root, text="Login URL:", font=("Arial", 10, "bold")).pack(pady=5)
        url_entry = tk.Entry(root, width=45)
        url_entry.insert(0, os.getenv("LOGIN_URL", "https://sleepcare.ngrok.app/api/rooms/devices/login"))
        url_entry.pack()

        tk.Label(root, text="Device Token:", font=("Arial", 10, "bold")).pack(pady=5)
        token_entry = tk.Entry(root, width=45)
        token_entry.insert(0, os.getenv("DEVICE_TOKEN", ""))
        token_entry.pack()

        def on_submit():
            url = url_entry.get()
            token = token_entry.get()
            if not url or not token:
                messagebox.showerror("Error", "กรุณากรอกข้อมูลให้ครบ")
                return
            
            set_key(ENV_FILE, "LOGIN_URL", url)
            set_key(ENV_FILE, "DEVICE_TOKEN", token)
            root.destroy()

        tk.Button(root, text="🚀 START SYSTEM", command=on_submit, bg="#2ecc71", fg="white", font=("Arial", 12, "bold"), height=2).pack(pady=30)
        root.mainloop()

    # --- 2. Login Process ---
    def login(self):
        url = os.getenv("LOGIN_URL")
        token = os.getenv("DEVICE_TOKEN")
        
        login_payload = {
            "device_token": token
        }
        
        print(f"🔐 Attempting Login to: {url}")
        try:
            response = requests.post(url, json=login_payload, timeout=10)
            response.raise_for_status()
            
            self.config = response.json()
            print("✅ Login Success! Config received.")
            return True
        except Exception as e:
            print(f"❌ Login Failed: {e}")
            messagebox.showerror("Login Error", f"ไม่สามารถเข้าสู่ระบบได้:\n{e}")
            return False

    # --- 3. MQTT Management ---
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            print(f"📩 Server Command Received: {data}")
            if data.get("alert") == True:
                print(data.get("message"))
                if data.get("alert") == "warning":
                    # เล่น Buzzer สัก 3 ครั้ง
                else:
                    # เล่น Buzzer ยาวๆ
        except Exception as e:
            print(f"MQTT Msg Error: {e}")

    def start_mqtt(self):
        conf = self.config
        self.mqtt_client = mqtt.Client()
        
        auth = conf.get("mqtt_auth", {})
        if auth:
            self.mqtt_client.username_pw_set(auth.get("username"), auth.get("password"))
        
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(conf["mqtt_host"], conf["mqtt_port"], 60)
        
        # Subscribe
        sub_topic = f"device/{conf['device_id']}/command"
        self.mqtt_client.subscribe(sub_topic)
        self.mqtt_client.loop_start()
        print(f"📡 MQTT Connected. Topic: {conf['mqtt_topic']}")

    # --- 4. Sensor Reading Loop (Thread) ---
    def update_sensors_loop(self):
        while self.running:
            try:
                lux = read_light()
                temp, hum, pres, gas = read_bme()
                camera_status = self.camera_detector.detect()
                radar_status = self.radar_detector.detect()
                now_utc = datetime.now(timezone.utc).isoformat()

                # Internal State Update
                self.current_data = {
                    "temperature_c": round(temp, 2),
                    "humidity_pct": round(hum, 2),
                    "pressure_hpa": round(pres, 2),
                    "altitude_m": round(gas, 2),
                    "lux": round(lux, 2),
                    "camera_motion_state": camera_status,
                    "radar_motion_state": radar_status,
                    "help_voice_detected": False, 
                    "emergency_button_pressed": False,
                    "captured_at": now_utc
                }
                #  OLED Display Update
                self.oled.show_all(lux, temp, hum, pres, gas)
            except Exception as e:
                print(f"Sensor Reading Error: {e}")
            time.sleep(2)

    # --- 5. Main Control Loop ---
    def run(self):
        self.show_setup_gui() # 1. Token
        if not self.login(): # 2. Login with Body { "device_token": "..." }
            return

        self.start_mqtt() # 3. Connect MQTT
        self.running = True
        
        sensor_thread = threading.Thread(target=self.update_sensors_loop, daemon=True)
        sensor_thread.start()

        interval = self.config.get("env_log_interval_sec", 120)
        pub_topic = self.config.get("mqtt_topic")

        print(f"🚀 System Online! Logging every {interval}s")
        try:
            while True:
                if self.current_data:
                    mqtt_payload = self.current_data.copy()
                    mqtt_payload["device_id"] = self.config["device_id"]
                    
                    self.mqtt_client.publish(pub_topic, json.dumps(mqtt_payload))
                    print(f"📤 Published to {pub_topic}")
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("🛑 Stopping...")
            self.running = False
            self.mqtt_client.loop_stop()
            self.camera_detector.close()

if __name__ == "__main__":
    app = DeviceApp()
    app.run()