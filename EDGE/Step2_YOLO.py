import cv2
from ultralytics import YOLO

# Load YOLOv8 (pretrained COCO model)
model = YOLO("yolov8n.pt")  # nano version (fastest)

# Classes of interest for Lost & Found
INTEREST_CLASSES = ["backpack", "handbag", "suitcase", "laptop", "cell phone", "book"]

# Open webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame")
        break

    # Run YOLOv8 detection
    results = model(frame, conf=0.4)  # confidence threshold

    for box in results[0].boxes:
        cls_id = int(box.cls[0])   # class id
        conf = float(box.conf[0])  # confidence
        x1, y1, x2, y2 = map(int, box.xyxy[0])  # bbox
        label = model.names[cls_id]

        if label in INTEREST_CLASSES or label == "person":
            # Draw detection
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Show frame
    cv2.imshow("YOLOv8 Detection", frame)

    # Exit on ESC
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
