import cv2
import mediapipe as mp
import numpy as np
import time
import winsound
import threading

#  TUNED THRESHOLDS (based on the testing so far)
EAR_THRESHOLD      = 0.27   # tuned for your EAR range 0.29-0.32
NOD_THRESHOLD      = 0.18   # tuned for your vertical ratio 0.20-0.25
CLOSED_FRAMES_MAX  = 48     # ~2 seconds to trigger eye alert
NOD_FRAMES_MAX     = 48     # ~2 seconds to trigger nod alert

# Eye landmark indices (MediaPipe)
LEFT_EYE  = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

#  EAR CALCULATION
def calculate_ear(landmarks, eye_points, w, h):
    pts = [(landmarks[i].x * w, landmarks[i].y * h) for i in eye_points]
    A = np.linalg.norm(np.array(pts[1]) - np.array(pts[5]))
    B = np.linalg.norm(np.array(pts[2]) - np.array(pts[4]))
    C = np.linalg.norm(np.array(pts[0]) - np.array(pts[3]))
    return (A + B) / (2.0 * C)

#  SETUP
mp_face = mp.solutions.face_mesh
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Counters
closed_counter = 0
nod_counter    = 0

# Blink rate tracking
blink_count        = 0
blink_window_start = time.time()
blink_rate         = 0
eye_was_closed     = False
BLINK_WINDOW       = 60    # measure blinks per 60 seconds
LOW_BLINK_RATE     = 10    # below this = drowsy
blink_alert        = False

# Alert states
eye_alert      = False
nod_alert      = False

# Alert cooldown (prevents spam)
last_alert_time = 0
ALERT_COOLDOWN  = 3  # seconds

def play_alert_sound():
    for _ in range(3):  # beep 3 times
        winsound.Beep(1000, 500)  # frequency=1000Hz, duration=500ms
        time.sleep(0.2)
print("PowerPenguin Drowsiness Detector Started")
print("Press Q to quit")
print("─" * 40)

#  MAIN LOOP
with mp_face.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as face_mesh:

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        # Default status
        status       = "AWAKE"
        status_color = (0, 255, 0)

        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0].landmark

            # EAR Calculation 
            left_ear  = calculate_ear(lm, LEFT_EYE, w, h)
            right_ear = calculate_ear(lm, RIGHT_EYE, w, h)
            avg_ear   = (left_ear + right_ear) / 2.0

            # Head Pose Calculation
            nose     = lm[1]
            chin     = lm[152]
            vertical_ratio = chin.y - nose.y

            # Eye Drowsiness Logic 
            if avg_ear < EAR_THRESHOLD:
                closed_counter += 1
                eye_was_closed = True
            else:
                # Eye just opened - count as one complete blink
                if eye_was_closed:
                    blink_count += 1
                    eye_was_closed = False
                closed_counter = 0
                eye_alert      = False

            if closed_counter >= CLOSED_FRAMES_MAX:
                eye_alert = True

            # Blink Rate Calculation
            current_window_time = time.time()
            elapsed = current_window_time - blink_window_start

            if elapsed > BLINK_WINDOW:
                # Calculate blinks per minute
                blink_rate = blink_count
                blink_count = 0
                blink_window_start = current_window_time

                if blink_rate < LOW_BLINK_RATE:
                    blink_alert = True
                    print(f"[ALERT] Low blink rate detected: {blink_rate} blinks/min")
                else:
                    blink_alert = False

            # Head Nod Logic 
            if vertical_ratio < NOD_THRESHOLD:
                nod_counter += 1
            else:
                nod_counter = 0
                nod_alert   = False

            if nod_counter >= NOD_FRAMES_MAX:
                nod_alert = True

            # Combined Alert
            current_time = time.time()
            if eye_alert or nod_alert or blink_alert:
                status       = "DROWSY!"
                status_color = (0, 0, 255)

                # Log alert to console (with cooldown)
                if current_time - last_alert_time > ALERT_COOLDOWN:
                    if eye_alert:
                        print(f"[ALERT] Eyes closed too long! EAR={avg_ear:.2f}")
                    if nod_alert:
                        print(f"[ALERT] Head nodding detected! Ratio={vertical_ratio:.2f}")
                    if blink_alert:
                        print(f"[ALERT] Low blink rate detected: {blink_rate} blinks/min")
                    last_alert_time = current_time
                    threading.Thread(target=play_alert_sound, daemon=True).start()

            # UI Stuffs

            # Red border when drowsy
            if eye_alert or nod_alert or blink_alert:
                cv2.rectangle(frame, (0, 0), (w, h), (0, 0, 255), 10)

            # Status banner at top
            cv2.rectangle(frame, (0, 0), (w, 50), (0, 0, 0), -1)
            cv2.putText(frame, f"PowerPenguin  |  Status: {status}", (10, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, status_color, 2)

            # EAR value
            ear_color = (0, 255, 0) if avg_ear > EAR_THRESHOLD else (0, 0, 255)
            cv2.putText(frame, f"EAR: {avg_ear:.2f}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, ear_color, 2)

            # Eye closed counter
            cv2.putText(frame, f"Eye Closed Frames: {closed_counter}/{CLOSED_FRAMES_MAX}", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            # Head ratio
            nod_color = (0, 255, 0) if vertical_ratio > NOD_THRESHOLD else (0, 165, 255)
            cv2.putText(frame, f"Head Ratio: {vertical_ratio:.2f}", (10, 150),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, nod_color, 2)

            # Nod counter
            cv2.putText(frame, f"Nod Frames: {nod_counter}/{NOD_FRAMES_MAX}", (10, 180),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # Blink rate
            blink_color = (0, 255, 0) if blink_rate >= LOW_BLINK_RATE or blink_rate == 0 else (0, 0, 255)
            time_remaining = int(BLINK_WINDOW - (time.time() - blink_window_start))
            cv2.putText(frame, f"Blink Rate: {blink_rate} blinks/min", (10, 210),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, blink_color, 2)
            cv2.putText(frame, f"Blinks This Window: {blink_count} ({time_remaining}s left)", (10, 240),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            # Blink alert text
            if blink_alert:
                cv2.putText(frame, f"LOW BLINK RATE - WAKE UP!", (10, h - 80),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

            # Big alert text
            if eye_alert:
                cv2.putText(frame, "EYES CLOSED - WAKE UP!", (10, h - 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
            if nod_alert:
                cv2.putText(frame, "HEAD NODDING - WAKE UP!", (10, h - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 3)

        else:
            # No face detected
            cv2.rectangle(frame, (0, 0), (w, 50), (0, 0, 0), -1)
            cv2.putText(frame, "PowerPenguin  |  No Face Detected", (10, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        cv2.imshow("PowerPenguin - Drowsiness Detector", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
print("PowerPenguin stopped.")