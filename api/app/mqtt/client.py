import paho.mqtt.client as mqtt
import os
import json
from app.services.environment_service import EnvironmentService
from app.core.database import SessionLocal

class MQTTManager:
    def __init__(self):
        self.client = mqtt.Client()
        self.subscribed = set()
        self.client.on_message = self.on_message
        username = os.getenv("MQTT_USERNAME")
        password = os.getenv("MQTT_PASSWORD")
        if username:
            self.client.username_pw_set(username, password)
        self.client.connect(
            os.getenv("MQTT_HOST"),
            int(os.getenv("MQTT_PORT"))
        )
        self.client.loop_start()

    def subscribe(self, topic: str):
        if topic in self.subscribed:
            return
        print("Subscribe topic:", topic)
        self.client.subscribe(topic)
        self.subscribed.add(topic)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            topic = msg.topic
            db = SessionLocal()
            try:
                EnvironmentService.process(
                    db=db,
                    topic=topic,
                    payload=payload
                )
            finally:
                db.close()
        except Exception as e:
            print("MQTT message error:", e)

mqtt_manager: MQTTManager | None = None

def get_mqtt():
    global mqtt_manager
    if mqtt_manager is None:
        mqtt_manager = MQTTManager()
    return mqtt_manager