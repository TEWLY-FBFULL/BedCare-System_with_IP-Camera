import cv2
import mediapipe as mp
from app.ai.analyze_sleeping_posture import (
    analyze_supine,
    analyze_prone,
    analyze_side
)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=0,
    min_detection_confidence=0.3,
    min_tracking_confidence=0.3
)

def calculate_posture_metrics(frame, posture):
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)
    if not results.pose_landmarks:
        print(f"⚠️ Mediapipe could not detect pose landmarks for {posture}")
        return None, {}, 0
    lm = results.pose_landmarks.landmark
    if posture == "Supine":
        quality, metrics, score = analyze_supine(
            lm,
            mp_pose=mp_pose,
            frame_shape=frame.shape
        )
    elif posture == "Prone":
        quality, metrics, score = analyze_prone(
            lm,
            mp_pose=mp_pose,
            frame_shape=frame.shape
        )
    else:
        side = "left" if "To-Left" in posture else "right"
        quality, metrics, score = analyze_side(
            lm,
            side=side,
            mp_pose=mp_pose,
            frame_shape=frame.shape
        )
    print(f"Posture: {posture}, Quality: {quality}, Score: {score:.2f}")
    return quality, metrics, score