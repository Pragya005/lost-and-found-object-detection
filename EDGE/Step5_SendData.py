import cv2
import time
import os
import json
import base64
import paho.mqtt.client as mqtt
from ultralytics import YOLO
import socket
DEVICE_ID = socket.gethostname().upper()

# MQTT Setup
BROKER = "localhost"
PORT = 1883
TOPIC = "edge/fog/unattended"

client = mqtt.Client()
client.connect(BROKER, PORT, 60)

# Load YOLOv8 models
model_items = YOLO(r"C:\Users\aryan\ai-lost-and-found-object-detection\best.pt")
model_person = YOLO("yolov8l.pt")

# Classes of interest
INTEREST_CLASSES = [
    'bag', 'laptop', 'mobile', 'mouse', 'glasses', 'gloves', 'pendent',
    'watch', 'book', 'pen', 'eraser', 'stapler', 'scale', 'pencil box',
    'sharpener', 'coin', 'bottle', 'cap'
]

UNATTENDED_TIME = 10
PERSON_PROXIMITY = 100
tracked_objects = {}

SNAPSHOT_DIR = "snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

cap = cv2.VideoCapture(1)
if not cap.isOpened():
    print("❌ Cannot open camera")
    exit()

frame_count = 0
results_person = None

print("✅ Camera started. Press ESC to exit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    now = time.time()
    annotated_frame = frame.copy()
    frame_count += 1

    if frame_count % 3 == 0:
        results_person = model_person.track(
            source=frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=0.45,
            verbose=True  # 👈 enabled YOLO logs
        )

    results_items = model_items.track(
        source=frame,
        persist=True,
        tracker="bytetrack.yaml",
        conf=0.6,
        verbose=True  # 👈 enabled YOLO logs
    )

    persons, objects = [], []

    if results_person and results_person[0].boxes is not None:
        for box in results_person[0].boxes:
            cls_id = int(box.cls[0])
            label = model_person.names[cls_id]
            if label == "person":
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                pid = int(box.id[0]) if box.id is not None else -1
                persons.append(((x1, y1, x2, y2), pid))

    if results_items and results_items[0].boxes is not None:
        for box in results_items[0].boxes:
            cls_id = int(box.cls[0])
            label = model_items.names[cls_id]
            if label in INTEREST_CLASSES:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                oid = int(box.id[0]) if box.id is not None else -1
                objects.append(((x1, y1, x2, y2), oid, label))

    for (x1, y1, x2, y2), oid, label in objects:
        if oid not in tracked_objects:
            tracked_objects[oid] = {
                "label": label,
                "last_seen": now,
                "last_person_near": now,
                "snapshot_taken": False
            }
        else:
            tracked_objects[oid]["last_seen"] = now

        person_near = False
        nearest_person_id = None
        min_dist = float("inf")

        for (px1, py1, px2, py2), pid in persons:
            ox, oy = (x1 + x2) // 2, (y1 + y2) // 2
            px, py = (px1 + px2) // 2, (py1 + py2) // 2
            dist = ((ox - px) ** 2 + (oy - py) ** 2) ** 0.5
            if dist < min_dist:
                min_dist = dist
                nearest_person_id = pid
            if dist < PERSON_PROXIMITY:
                tracked_objects[oid]["last_person_near"] = now
                tracked_objects[oid]["snapshot_taken"] = False
                person_near = True

        unattended_time = now - tracked_objects[oid]["last_person_near"]

        if unattended_time > UNATTENDED_TIME:
            color = (0, 0, 255)
            status = "UNATTENDED"

            if not tracked_objects[oid]["snapshot_taken"]:
                crop = frame[y1:y2, x1:x2]
                filename = f"{label}_O{oid}_nearP{nearest_person_id}_{int(now)}.jpg"
                filepath = os.path.join(SNAPSHOT_DIR, filename)
                cv2.imwrite(filepath, crop)
                print(f"📸 Snapshot saved: {filepath}")

                with open(filepath, "rb") as img_file:
                    img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

                detection_data = {
                    "device_id" : DEVICE_ID,
                    "object_id": oid,
                    "label": label,
                    "status": status,
                    "nearest_person_id": nearest_person_id,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "snapshot_name": filename,
                    "image": img_base64
                }

                client.publish(TOPIC, json.dumps(detection_data))
                print(f"📤 Sent to Fog Node: {detection_data}")

                tracked_objects[oid]["snapshot_taken"] = True
        else:
            color = (0, 255, 0)
            status = "Attended"

        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            annotated_frame,
            f"{label} OID:{oid} {status}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

    for (x1, y1, x2, y2), pid in persons:
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
        cv2.putText(
            annotated_frame,
            f"Person PID:{pid}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2
        )

    cv2.imshow("YOLOv8 + MQTT Edge Node (Dual Model with IDs)", annotated_frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
