import cv2
import math
import time
import os
import subprocess
import mediapipe as mp


def calculate_angle(p1, p2):
    """
    Calculates the angle in degrees between two points.
    """
    radians = math.atan2(p2.y - p1.y, p2.x - p1.x)
    angle = math.degrees(radians)
    return abs(angle)

def get_posture():
    # Initializing MediaPipe
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    # Initializing webcam
    cap = cv2.VideoCapture(0)

    bad_posture_start_time = 0
    TIME_THRESHOLD = 3

    last_alert_time = 0
    ALERT_COOLDOWN = 3.0

    # Calibration, Tolerance, and Pause variables
    baseline_posture = None
    TOLERANCE_DROP = 0.85   
    TOLERANCE_ANGLE = 7.0
    TOLERANCE_FORWARD = 0.05   
    is_paused = False       # <--- Pause variable


    print("System starting; take good posture then press 'c'")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Can't access webcam!")
            break

        # Read keyboard input immediately!
        key = cv2.waitKey(10) & 0xFF

        # 'q' key to quit
        if key == ord('q'):
            break

        # 'p' key to pause / resume
        if key == ord('p'):
            is_paused = not is_paused
            if is_paused:
                print("System PAUSED.")
            else:
                print(f"System RESUMED")
                bad_posture_start_time = 0

        # --- PAUSE LOGIC ---
        if is_paused:
            image_paused = frame.copy()
            cv2.putText(image_paused, "PAUSED - Press 'p' to resume", (50, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.imshow('Checking Posture...', image_paused)
            continue # Skip MediaPipe processing and go to next frame
        # --------------------------

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        is_person_really_there = False
        landmarks = None

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            nose_visibility = landmarks[mp_pose.PoseLandmark.NOSE.value].visibility
            
            if nose_visibility > 0.5:
                is_person_really_there = True
        
        # IF A PERSON IS DETECTED IN THE FRAME
        if is_person_really_there:
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            landmarks = results.pose_landmarks.landmark

            nose_y = landmarks[mp_pose.PoseLandmark.NOSE.value].y
            left_shoulder_y = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
            right_shoulder_y = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y

            left_eye = landmarks[mp_pose.PoseLandmark.LEFT_EYE.value]
            right_eye = landmarks[mp_pose.PoseLandmark.RIGHT_EYE.value]
            left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

            left_ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR.value]
            right_ear = landmarks[mp_pose.PoseLandmark.RIGHT_EAR.value]

            # Calculate the average Z (depth) of ears and shoulders
            ears_z = (left_ear.z + right_ear.z) / 2
            shoulders_z = (left_shoulder.z + right_shoulder.z) / 2

            forward_head_distance = shoulders_z - ears_z

            mid_shoulder_y = (left_shoulder_y + right_shoulder_y) / 2
            head_drop = mid_shoulder_y - nose_y

            shoulder_width = math.hypot(left_shoulder.x - right_shoulder.x, left_shoulder.y - right_shoulder.y)
            
            if shoulder_width > 0.01:
                normalized_head_drop = head_drop / shoulder_width
            else:
                normalized_head_drop = head_drop
            
            head_angle = calculate_angle(left_eye, right_eye)
            shoulder_angle = calculate_angle(left_shoulder, right_shoulder)

            if baseline_posture is None:
                cv2.putText(image, "Press 'c' to calibrate", (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
                
                if key == ord('c'):
                    baseline_posture = {
                        'head_ang': head_angle,
                        'shoulder_ang': shoulder_angle,
                        'drop': normalized_head_drop,
                        'forward_head': forward_head_distance
                    }
                    print(f"Calibration complete!")
            
            else:

                

                dynamic_threshold_drop = baseline_posture['drop'] * TOLERANCE_DROP
                var_head_angle = abs(head_angle - baseline_posture['head_ang'])
                var_shoulder_angle = abs(shoulder_angle - baseline_posture['shoulder_ang'])
                is_forward_neck = (forward_head_distance - baseline_posture['forward_head']) > TOLERANCE_FORWARD

                cv2.putText(image, "Press 'q' to quit | 'p' to pause", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2, cv2.LINE_AA)
                cv2.putText(image, f"Head Var: {var_head_angle:.1f} deg", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                cv2.putText(image, f"Shoulder Var: {var_shoulder_angle:.1f} deg", (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

                is_bad_posture = (var_head_angle > TOLERANCE_ANGLE) or \
                                 (var_shoulder_angle > TOLERANCE_ANGLE) or \
                                 (normalized_head_drop < dynamic_threshold_drop) or\
                                 is_forward_neck          

                if is_bad_posture:
                    if bad_posture_start_time == 0:
                        bad_posture_start_time = time.time()
                    else:
                        elapsed_time = time.time() - bad_posture_start_time
                        if elapsed_time > TIME_THRESHOLD:
                            cv2.putText(image, "BAD POSTURE DETECTED", (50, 100),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3, cv2.LINE_AA)
                            
                            # Play Mac alert sound
                            if time.time() - last_alert_time > ALERT_COOLDOWN:
                                subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"])
                                last_alert_time = time.time()              

                else:
                    bad_posture_start_time = 0
                    cv2.putText(image, "POSTURE OK!", (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                    
                if key == ord('r'):
                    baseline_posture = None
                    print(f"Calibration reset needed.")

        # IF NO ONE IS DETECTED
        else:
            cv2.putText(image, "NO PERSON DETECTED", (50, 150), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3, cv2.LINE_AA)
            cv2.putText(image, "Press 'q' to quit | 'p' to pause", (30, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2, cv2.LINE_AA)
                        
            
            bad_posture_start_time = 0 

        # Show the frame
        cv2.imshow('Checking Posture...', image)

    # Cleanup on exit
    cv2.destroyAllWindows()
    cap.release()

# Run the program
if __name__ == "__main__":
    get_posture()
