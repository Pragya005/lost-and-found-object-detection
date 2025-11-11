import json
import paho.mqtt.client as mqtt
import base64
import time
from datetime import datetime, timedelta
from pymongo import MongoClient, ASCENDING

# MQTT Configuration
BROKER = "localhost"
PORT = 1883
TOPIC = "edge/fog/unattended"

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "fog_ai_detection"
COLLECTION_NAME = "events"
RETENTION_DAYS = 7

# Connect to MongoDB
client_db = MongoClient(MONGO_URI)
db = client_db[DB_NAME]
collection = db[COLLECTION_NAME]

# ✅ Create TTL index (auto-delete docs after 7 days)
# Only needs to be created once
collection.create_index(
    [("saved_at", ASCENDING)],
    expireAfterSeconds=RETENTION_DAYS * 24 * 60 * 60
)
print(f"✅ MongoDB connected. TTL set to {RETENTION_DAYS} days.")

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker.")
        client.subscribe(TOPIC)
    else:
        print(f"Failed to connect. Code {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        print("\n📩 Received event:")
        print(json.dumps(data, indent=4))

        # Prepare MongoDB document
        event_doc = {
            "device_id": data.get("device_id", "unknown"),
            "object_id": data.get("object_id", "unknown"),
            "label": data.get("label", "unknown"),
            "status": data.get("status", "unknown"),
            "timestamp": data.get("timestamp"),
            "image_base64": data.get("image", None),
            "saved_at": datetime.utcnow()
        }

        # Insert event into MongoDB
        collection.insert_one(event_doc)
        print("✅ Event stored in MongoDB.")

    except Exception as e:
        print(f"❌ Error processing message: {e}")

# MQTT Client Setup
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect(BROKER, PORT, 60)
mqtt_client.loop_forever()
