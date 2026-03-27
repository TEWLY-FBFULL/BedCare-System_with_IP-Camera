from app.ai.posture_metrics_map import POSTURE_METRICS
from app.ai.detector import detect_person
from app.ai.posture_classifier import classify_posture
from app.ai.pose_metrics import calculate_posture_metrics

def run_sleep_ai(frame):
    person = detect_person(frame)
    if not person:
        return None
    
    posture = classify_posture(frame)
    if not posture: return None
    label, conf = posture

    result = calculate_posture_metrics(frame, label)
    quality, metrics, score = result
    if quality is None or quality == "Invalid": 
        return None
  
    allowed_metrics = POSTURE_METRICS.get(label, [])
    filtered_metrics = {
        k: v for k, v in metrics.items()
        if k in allowed_metrics
    }
    return {
        "posture": {
            "label": label,
            "quality": quality,
            "confidence": conf
        },
        "metrics": {**filtered_metrics, "score": score},
        "score": score
    }