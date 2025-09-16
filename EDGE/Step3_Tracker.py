import cv2
from ultralytics import YOLO

# Load YOLOv8 model
model = YOLO("yolov8n.pt")  # use yolov8s.pt for better accuracy

# Define classes of interest
INTEREST_CLASSES = ["backpack", "handbag", "suitcase", "laptop", "cell phone", "book"]

# Open webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run YOLOv8 with ByteTrack tracker
    results = model.track(
        source=frame,
        persist=True,
        tracker="bytetrack.yaml",
        conf=0.6
    )

    annotated_frame = frame.copy()

    # Filter and draw only objects of interest
    if results[0].boxes is not None:
        for box in results[0].boxes:
            cls_id = int(box.cls[0])      # class id
            conf = float(box.conf[0])     # confidence
            label = model.names[cls_id]   # class name

            # Skip irrelevant classes
            if label not in INTEREST_CLASSES and label != "person":
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])  # bbox
            track_id = int(box.id[0]) if box.id is not None else -1

            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                annotated_frame,
                f"{label} ID:{track_id} Conf:{conf:.2f}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

    cv2.imshow("YOLOv8 + ByteTrack (Filtered)", annotated_frame)

    if cv2.waitKey(50) & 0xFF == 27:  # ESC key
        break

cap.release()
cv2.destroyAllWindows()
