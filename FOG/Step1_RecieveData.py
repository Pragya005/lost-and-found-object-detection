import json
import paho.mqtt.client as mqtt
import base64
import os
import time

BROKER = "localhost"
TOPIC = "edge/fog/unattended"

# When connected to MQTT broker
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker.")
    client.subscribe(TOPIC)
  

# Function to save image from base64 string
def save_snapshot(data):
    if "image" not in data:
        return

    try:
        # Prepare folder and filename
        save_dir = "received_snapshots"
        os.makedirs(save_dir, exist_ok=True)

        filename = f"{data['label']}_ID{data['object_id']}_{int(time.time())}.jpg"
        save_path = os.path.join(save_dir, filename)

        # Decode and save image
        img_data = base64.b64decode(data["image"])
        with open(save_path, "wb") as f:
            f.write(img_data)

        print(f"Image saved at: {os.path.abspath(save_path)}")

    except Exception as e:
        print(f"Error saving image: {e}")

# When message arrives from Edge node
def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    print("\nReceived unattended item from edge:")
    print(json.dumps(data, indent=4))

    # Save image if available
    save_snapshot(data)

# MQTT setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, 1883, 60)
client.loop_forever()
