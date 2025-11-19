import json
import paho.mqtt.client as mqtt
import base64
import time
import os
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
RETENTION_DAYS = 7  # auto-delete after 7 days

# Folder to save images
SAVE_DIR = "received_snapshots"
os.makedirs(SAVE_DIR, exist_ok=True)

# Connect to MongoDB
client_db = MongoClient(MONGO_URI)
db = client_db[DB_NAME]
collection = db[COLLECTION_NAME]

# ✅ Create TTL index (auto-delete after 7 days)
collection.create_index(
    [("ttl_expire_at", ASCENDING)],
    expireAfterSeconds=RETENTION_DAYS * 24 * 60 * 60
)
print(f"✅ MongoDB connected. TTL set to {RETENTION_DAYS} days.\n")


def save_snapshot(data):
    """Save Base64 image and return path with forward slashes."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        save_dir = os.path.join(base_dir, "received_snapshots")
        os.makedirs(save_dir, exist_ok=True)

        filename = data.get("snapshot_name", f"{data['label']}_ID{data['object_id']}_{int(time.time())}.jpg")
        save_path = os.path.join(save_dir, filename)

        img_data = base64.b64decode(data["image"])
        with open(save_path, "wb") as f:
            f.write(img_data)

        clean_path = save_path.replace("\\", "/")
        print(f"📸 Image saved: {clean_path}")
        return clean_path

    except Exception as e:
        print(f"❌ Error saving image: {e}")
        return None


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker.")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Failed to connect. Code {rc}")


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        # Extract Base64 BEFORE popping so we don't lose it
        image_base64 = data.get("image")

        # Save snapshot to disk if image exists
        image_path = None
        if image_base64:
            image_path = save_snapshot({
                **data,
                "image": image_base64
            })

        # Remove the image field so data only contains metadata
        data.pop("image", None)

        # TTL cleanup time
        ttl_expire_at = datetime.utcnow() + timedelta(days=RETENTION_DAYS)

        print("\n📩 Received unattended item from Edge:")
        for key, value in data.items():
            print(f"  {key}: {value}")

        # FINAL DOCUMENT (correct)
        event_doc = {
            "device_id": data.get("device_id", "unknown"),
            "object_id": data.get("object_id", "unknown"),
            "label": data.get("label", "unknown"),
            "status": data.get("status", "unknown"),
            "timestamp": data.get("timestamp"),
            "snapshot_name": data.get("snapshot_name"),
            "image_path": image_path,
            "image_base64": image_base64,
            "saved_at": datetime.utcnow(),
            "collected": False
        }

        collection.insert_one(event_doc)
        print(f"✅ Event stored in MongoDB with base64 and image path\n")

    except Exception as e:
        print(f"❌ Error processing message: {e}")



# MQTT setup
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(BROKER, PORT, 60)
    mqtt_client.loop_forever()
except Exception as e:
    print(f"❌ MQTT connection error: {e}")
