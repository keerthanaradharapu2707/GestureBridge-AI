import subprocess
import cv2
import mediapipe as mp
import time
import os
import math
import pyttsx3
import threading
import queue

from gesture_database import save_gesture


# ==========================================
# 1. MODEL CONFIGURATION
# ==========================================

MODEL_PATH = os.path.join("models", "hand_landmarker.task")

if not os.path.exists(MODEL_PATH):
    print("ERROR: Hand model not found!")
    print("Expected location:", MODEL_PATH)
    raise SystemExit


# ==========================================
# 2. GESTURE AND DATABASE SETTINGS
# ==========================================

VALID_GESTURES = {
    "Thumbs Up",
    "Open Palm",
    "Fist",
    "Peace Sign",
    "OK Sign"
}

GESTURE_STABLE_SECONDS = 0.7

last_detected_gesture = ""
gesture_start_time = 0.0
last_saved_gesture = ""


# ==========================================
# 3. TEXT-TO-SPEECH CONFIGURATION
# ==========================================

speech_queue = queue.Queue()

candidate_gesture = ""
candidate_start_time = 0.0
last_queued_gesture = ""
no_hand_start_time = None

GESTURE_VOICE_STABLE_SECONDS = 0.7
NO_HAND_RESET_SECONDS = 1.5



def speech_worker():
    while True:
        message = speech_queue.get()

        try:
            if message is None:
                break

            print("Speaking:", message)

            safe_message = message.replace("'", "''")

            powershell_script = (
                "Add-Type -AssemblyName System.Speech; "
                "$speaker = New-Object "
                "System.Speech.Synthesis.SpeechSynthesizer; "
                "$speaker.Volume = 100; "
                "$speaker.Rate = 0; "
                f"$speaker.Speak('{safe_message}'); "
                "$speaker.Dispose()"
            )

            subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    powershell_script,
                ],
                check=True,
                timeout=30,
                capture_output=True,
                text=True,
            )

        except Exception as error:
            print("Speech error:", error)

        finally:
            speech_queue.task_done()



def speak_gesture(gesture):
    """Queue each stable gesture once."""

    global candidate_gesture
    global candidate_start_time
    global last_queued_gesture
    global no_hand_start_time

    current_time = time.monotonic()

    # Handle missing or unrecognized hand gestures.
    if gesture not in VALID_GESTURES:
        candidate_gesture = ""
        candidate_start_time = 0.0

        if no_hand_start_time is None:
            no_hand_start_time = current_time

        elif (
            current_time - no_hand_start_time
            >= NO_HAND_RESET_SECONDS
        ):
            last_queued_gesture = ""

        return

    no_hand_start_time = None

    # Start timing when a different gesture appears.
    if gesture != candidate_gesture:
        candidate_gesture = gesture
        candidate_start_time = current_time
        return

    # Wait for the gesture to remain stable.
    if (
        current_time - candidate_start_time
        < GESTURE_VOICE_STABLE_SECONDS
    ):
        return

    # Avoid repeating the same gesture continuously.
    if gesture == last_queued_gesture:
        return

    # Remember and queue the new gesture.
    last_queued_gesture = gesture
    speech_queue.put(gesture)

    print("Voice announcement queued:", gesture)


# Start the voice worker AFTER defining the function.
speech_thread = threading.Thread(
    target=speech_worker,
    daemon=True
)
speech_thread.start()


# ==========================================
# 4. MEDIAPIPE CONFIGURATION
# ==========================================

options = mp.tasks.vision.HandLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(
        model_asset_path=MODEL_PATH
    ),
    running_mode=mp.tasks.vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)


# ==========================================
# 5. GESTURE RECOGNITION
# ==========================================

def distance(a, b):
    return math.hypot(
        a.x - b.x,
        a.y - b.y
    )


def recognize_gesture(hand):
    wrist = hand[0]
    thumb_tip = hand[4]
    thumb_joint = hand[3]
    index_tip = hand[8]

    # Detect extended fingers.
    index_up = hand[8].y < hand[6].y
    middle_up = hand[12].y < hand[10].y
    ring_up = hand[16].y < hand[14].y
    little_up = hand[20].y < hand[18].y

    fingers = [
        index_up,
        middle_up,
        ring_up,
        little_up
    ]

    # OK Sign.
    if (
        distance(thumb_tip, index_tip) < 0.07
        and middle_up
        and ring_up
        and little_up
    ):
        return "OK Sign"

    # Open Palm.
    if all(fingers):
        return "Open Palm"

    # Peace Sign.
    if (
        index_up
        and middle_up
        and not ring_up
        and not little_up
    ):
        return "Peace Sign"

    # Fist or Thumbs Up.
    if not any(fingers):
        thumb_extended = (
            distance(thumb_tip, wrist)
            > distance(thumb_joint, wrist) * 1.15
        )

        if thumb_extended:
            return "Thumbs Up"

        return "Fist"

    return "Gesture Not Recognized"


# ==========================================
# 6. DATABASE HISTORY SAVING
# ==========================================

def process_gesture_for_database(gesture):
    """Save a stable gesture once to MongoDB."""

    global last_detected_gesture
    global gesture_start_time
    global last_saved_gesture

    current_time = time.monotonic()

    # Ignore unrecognized gestures.
    if gesture not in VALID_GESTURES:
        last_detected_gesture = ""
        gesture_start_time = current_time
        last_saved_gesture = ""
        return

    # Start timing when a new gesture appears.
    if gesture != last_detected_gesture:
        last_detected_gesture = gesture
        gesture_start_time = current_time
        return

    # Wait for a stable gesture.
    if (
        current_time - gesture_start_time
        < GESTURE_STABLE_SECONDS
    ):
        return

    # Save only once until the gesture changes.
    if gesture != last_saved_gesture:
        try:
            saved = save_gesture(gesture)

            if saved:
                print("Gesture saved to MongoDB:", gesture)
                last_saved_gesture = gesture
            else:
                print("Gesture was not saved:", gesture)

        except Exception as error:
            print("Database saving error:", error)


# ==========================================
# 7. START WEBCAM
# ==========================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Could not open webcam.")

    speech_queue.put(None)
    speech_thread.join(timeout=3)

    raise SystemExit

print("====================================")
print("       GESTUREBRIDGE AI")
print("====================================")
print("Webcam detection started.")
print("Supported gestures:")
print("1. Thumbs Up")
print("2. Open Palm")
print("3. Fist")
print("4. Peace Sign")
print("5. OK Sign")
print("------------------------------------")
print("Voice output: Enabled")
print("MongoDB history: Enabled")
print("Press Q to close the camera.")
print("====================================")


# ==========================================
# 8. MAIN DETECTION LOOP
# ==========================================

try:
    with mp.tasks.vision.HandLandmarker.create_from_options(
        options
    ) as landmarker:

        start_time = time.monotonic()
        last_timestamp = -1

        while True:
            success, frame = cap.read()

            if not success:
                print("Unable to read webcam.")
                break

            # Mirror the camera view.
            frame = cv2.flip(frame, 1)

            rgb_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_frame
            )

            timestamp = int(
                (time.monotonic() - start_time) * 1000
            )

            timestamp = max(
                timestamp,
                last_timestamp + 1
            )

            last_timestamp = timestamp

            result = landmarker.detect_for_video(
                mp_image,
                timestamp
            )

            gesture = "Show your hand"

            if result.hand_landmarks:
                hand = result.hand_landmarks[0]

                # Recognize the current gesture.
                gesture = recognize_gesture(hand)

                # Voice output.
                speak_gesture(gesture)

                # Save stable gestures to MongoDB.
                process_gesture_for_database(gesture)

                height, width, _ = frame.shape

                # Draw hand connections.
                for connection in (
                    mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS
                ):
                    start_point = hand[connection.start]
                    end_point = hand[connection.end]

                    p1 = (
                        int(start_point.x * width),
                        int(start_point.y * height)
                    )

                    p2 = (
                        int(end_point.x * width),
                        int(end_point.y * height)
                    )

                    cv2.line(
                        frame,
                        p1,
                        p2,
                        (0, 255, 0),
                        2
                    )

                # Draw hand landmarks.
                for point in hand:
                    x = int(point.x * width)
                    y = int(point.y * height)

                    cv2.circle(
                        frame,
                        (x, y),
                        4,
                        (0, 255, 255),
                        -1
                    )

            else:
                # Allow voice state to reset when the hand disappears.
                speak_gesture(None)

                last_detected_gesture = ""
                last_saved_gesture = ""
                gesture_start_time = time.monotonic()

            # Display the gesture label.
            cv2.rectangle(
                frame,
                (10, 10),
                (frame.shape[1] - 10, 70),
                (30, 30, 30),
                -1
            )

            cv2.putText(
                frame,
                "Gesture: " + gesture,
                (20, 48),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                "Press Q to quit",
                (20, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            cv2.imshow(
                "GestureBridge AI - Gesture Recognition",
                frame
            )

            # Press Q to exit.
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

finally:
    # Release webcam resources.
    cap.release()
    cv2.destroyAllWindows()

    # Stop the speech worker safely.
    if speech_thread.is_alive():
        speech_queue.put(None)
        speech_thread.join(timeout=5)

    print("GestureBridge AI stopped.")
