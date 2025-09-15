import cv2

# 0 = default webcam, or replace with video path / IP camera URL
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()   # Capture frame-by-frame
    if not ret:
        print("❌ Failed to grab frame")
        break

    # Show the raw video stream (for testing only)
    cv2.imshow("Raw Camera Feed", frame)

    # Press ESC (27) to exit
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
