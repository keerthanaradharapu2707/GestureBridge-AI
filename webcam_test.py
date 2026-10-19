
import cv2

# Open the default laptop webcam
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open webcam.")
    print("Close other apps using the camera and try again.")
    raise SystemExit

print("Webcam opened successfully!")
print("Press Q to close the camera window.")

while True:
    success, frame = camera.read()

    if not success:
        print("Could not read a frame from the webcam.")
        break

    # Mirror the video, like a selfie camera
    frame = cv2.flip(frame, 1)

    cv2.putText(
        frame,
        "GestureBridge AI - Webcam Test",
        (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.imshow("GestureBridge AI - Webcam Test", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
