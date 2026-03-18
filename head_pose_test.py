import cv2
import mediapipe as mp
import numpy as np

mp_face = mp.solutions.face_mesh
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

# Head pose settings
NOD_THRESHOLD    = 0.15   # vertical tilt threshold
TILT_THRESHOLD   = 0.15   # side tilt threshold
NOD_FRAMES       = 48     # frames before nod alert (~2 sec)
nod_counter      = 0
nod_alert        = False

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

            # Key landmarks
            nose      = lm[1]    
            chin      = lm[152] 
            left_eye  = lm[33]   
            right_eye = lm[263]  
            forehead  = lm[10]   

            # Vertical tilt (nodding forward)
            vertical_ratio = chin.y - nose.y
            # Normal upright head: chin.y - nose.y is larger
            # Head drooping forward: ratio gets smaller

            # Horizontal tilt (head tilting sideways)
            horizontal_ratio = abs(left_eye.y - right_eye.y)

            # Detecting head nod 
            if vertical_ratio < NOD_THRESHOLD:
                nod_counter += 1
            else:
                nod_counter = 0
                nod_alert   = False

            if nod_counter >= NOD_FRAMES:
                nod_alert = True

            # for displaying values 
            cv2.putText(frame, f"Vertical Ratio: {vertical_ratio:.2f}", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            cv2.putText(frame, f"Horizontal Ratio: {horizontal_ratio:.2f}", (30, 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            cv2.putText(frame, f"Nod Frames: {nod_counter}", (30, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

            # Head status 
            if nod_alert:
                cv2.rectangle(frame, (0, 0), (w, h), (0, 165, 255), 8)
                cv2.putText(frame, "HEAD NOD ALERT!", (30, 170),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 165, 255), 3)
            elif horizontal_ratio > TILT_THRESHOLD:
                cv2.putText(frame, "Head Tilting Sideways", (30, 170),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
            else:
                cv2.putText(frame, "Head Position: NORMAL", (30, 170),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Drawing key landmark dots
            for point in [nose, chin, left_eye, right_eye, forehead]:
                px = int(point.x * w)
                py = int(point.y * h)
                cv2.circle(frame, (px, py), 5, (0, 255, 255), -1)

        else:
            cv2.putText(frame, "No Face Detected", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("Head Pose Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()