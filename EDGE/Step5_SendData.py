import cv2
import time
import os
import json
import base64
import paho.mqtt.client as mqtt
from ultralytics import YOLO

# MQTT Setup
BROKER = "localhost"       # use IP of Fog device if different system
PORT = 1883
TOPIC = "edge/fog/unattended"

client = mqtt.Client()
client.connect(BROKER, PORT, 60)

# Load YOLOv8 model
model = YOLO("yolov8m.pt")

# Classes of interest
INTEREST_CLASSES = ["backpack", "handbag", "suitcase", "laptop", "cell phone", "book"]

# Parameters
UNATTENDED_TIME = 10   # seconds before object is considered lost
PERSON_PROXIMITY = 100 # pixels for "nearby" check

# Tracking dictionary
tracked_objects = {}

# Folder for saving snapshots
SNAPSHOT_DIR = "snapshots"
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1) #mirror video

    # Run YOLOv8 + ByteTrack
    results = model.track(
        source=frame,
        persist=True,
        tracker="bytetrack.yaml",
        conf=0.6
    )

    now = time.time()
    annotated_frame = frame.copy()

    persons = []
    objects = []

    # Step 1: Collect detections
    if results[0].boxes is not None:
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            track_id = int(box.id[0]) if box.id is not None else -1

            if label == "person":
                persons.append(((x1, y1, x2, y2), track_id))
            elif label in INTEREST_CLASSES:
                objects.append(((x1, y1, x2, y2), track_id, label))

    # Step 2: Update tracking dictionary for objects
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

        # Check proximity with persons
        person_near = False
        for (px1, py1, px2, py2), pid in persons:
            ox, oy = (x1 + x2) // 2, (y1 + y2) // 2
            px, py = (px1 + px2) // 2, (py1 + py2) // 2
            dist = ((ox - px) ** 2 + (oy - py) ** 2) ** 0.5
            if dist < PERSON_PROXIMITY:
                tracked_objects[oid]["last_person_near"] = now
                tracked_objects[oid]["snapshot_taken"] = False  # reset
                person_near = True
                break

        # Step 3: Check unattended condition
        unattended_time = now - tracked_objects[oid]["last_person_near"]
        if unattended_time > UNATTENDED_TIME:
            color = (0, 0, 255)  # Red for unattended
            status = "UNATTENDED"

            # Save snapshot only once
            if not tracked_objects[oid]["snapshot_taken"]:
                crop = frame[y1:y2, x1:x2]
                filename = f"{label}_ID{oid}_{int(now)}.jpg"
                filepath = os.path.join(SNAPSHOT_DIR, filename)
                cv2.imwrite(filepath, crop)
                print(f"Snapshot saved: {filepath}")
                
                # Convert image to Base64
                with open(filepath, "rb") as img_file:
                    img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

                # Prepare detection data
                detection_data = {
                    "object_id": oid,
                    "label": label,
                    "status": status,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "snapshot_name": filename,
                    "image": img_base64 
                }

                # Publish to fog node
                client.publish(TOPIC, json.dumps(detection_data))
                print(f"Sent to Fog Node: {detection_data}")

                tracked_objects[oid]["snapshot_taken"] = True


        else:
            color = (0, 255, 0)  # Green if attended
            status = "Attended"

        # Draw bounding box + status
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            annotated_frame,
            f"{label} ID:{oid} {status}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

    # Step 4: Draw persons
    for (x1, y1, x2, y2), pid in persons:
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
        cv2.putText(annotated_frame, f"Person ID:{pid}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    cv2.imshow("YOLOv8 + MQTT Edge Node", annotated_frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
