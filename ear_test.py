import cv2
import mediapipe as mp
import numpy as np

# Eye landmark indices for MediaPipe
LEFT_EYE  = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

def calculate_ear(landmarks, eye_points, w, h):
    pts = [(landmarks[i].x * w, landmarks[i].y * h) for i in eye_points]
    A = np.linalg.norm(np.array(pts[1]) - np.array(pts[5]))
    B = np.linalg.norm(np.array(pts[2]) - np.array(pts[4]))
    C = np.linalg.norm(np.array(pts[0]) - np.array(pts[3]))
    return (A + B) / (2.0 * C)

mp_face = mp.solutions.face_mesh
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

# Drowsiness settings
EAR_THRESHOLD   = 0.25   # below this = eyes closed
CLOSED_FRAMES   = 48     # frames before alert (~2 sec at 24fps)
closed_counter  = 0
alert_triggered = False

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
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0].landmark

            # Calculate EAR for both eyes
            left_ear  = calculate_ear(lm, LEFT_EYE, w, h)
            right_ear = calculate_ear(lm, RIGHT_EYE, w, h)
            avg_ear   = (left_ear + right_ear) / 2.0

            # Count closed frames
            if avg_ear < EAR_THRESHOLD:
                closed_counter += 1
            else:
                closed_counter  = 0
                alert_triggered = False

            # Trigger alert after 2 seconds
            if closed_counter >= CLOSED_FRAMES:
                alert_triggered = True

            # Display EAR value
            ear_color = (0, 255, 0) if avg_ear > EAR_THRESHOLD else (0, 0, 255)
            cv2.putText(frame, f"EAR: {avg_ear:.2f}", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, ear_color, 2)

            # Display closed frame counter
            cv2.putText(frame, f"Closed Frames: {closed_counter}", (30, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

            # Show drowsiness alert
            if alert_triggered:
                cv2.rectangle(frame, (0, 0), (w, h), (0, 0, 255), 8)
                cv2.putText(frame, "DROWSINESS ALERT!", (30, 140),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
            else:
                cv2.putText(frame, "Status: AWAKE", (30, 140),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        else:
            cv2.putText(frame, "No Face Detected", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("EAR Drowsiness Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()