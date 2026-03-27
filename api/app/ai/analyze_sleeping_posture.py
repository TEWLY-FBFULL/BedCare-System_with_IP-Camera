import numpy as np
from collections import deque

#  Global smoothing (moving average filter)
SMOOTH_QUEUE = {
    "supine": deque(maxlen=10),
    "prone": deque(maxlen=10),
    "side": deque(maxlen=10),
}

METRIC_DB_MAP = {
    "NeckTilt": "neck_tilt",
    "TrunkFlex": "trunk_flex",
    "AxialRot": "axial_rotation",
    "BodyTilt": "body_tilt",
    "NeckFlex": "neck_flex",
    "LatTilt": "lateral_tilt",
    "HeadRot": "head_rotation"
}

def get_quality_label(score):
    if score >= 85: return "good"
    if score >= 65: return "moderate"
    if score >= 45: return "poor"
    return "danger"

#  Helper Functions
def normalize_landmark(lm, frame_shape=None):
    if isinstance(lm, np.ndarray):
        return lm
    coords = np.array([[p.x, p.y] for p in lm])
    if frame_shape is not None:
        h, w = frame_shape[:2]
        coords[:, 0] *= w
        coords[:, 1] *= h
    
    ls, rs = coords[11], coords[12]
    shoulder_width = np.linalg.norm(ls - rs)
    if shoulder_width < 1e-4: 
        return None
    shoulder_center = (ls + rs) / 2
    return (coords - shoulder_center) / shoulder_width

def vector_angle(v1, v2):
    v1 = np.array(v1)
    v2 = np.array(v2)
    
    min_dim = min(len(v1), len(v2))
    v1 = v1[:min_dim]
    v2 = v2[:min_dim]

    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 < 1e-7 or norm2 < 1e-7:
        return 0.0
        
    dot_product = np.dot(v1, v2)
    cosang = dot_product / (norm1 * norm2)
    angle = np.degrees(np.arccos(np.clip(cosang, -1.0, 1.0)))
    return float(angle) if not np.isnan(angle) else 0.0

def wrap_angle(angle):
    """จำกัดมุมให้อยู่ในช่วง -180° ถึง 180°"""
    return (angle + 180) % 360 - 180

def posture_score(metrics, thresholds):
    score = 100
    penalty_per_metric = 100 / len(metrics) # กระจายน้ำหนักการหักคะแนน
    for key, value in metrics.items():
        if key not in thresholds:
            continue
        low, high = thresholds[key]
        if value < low or value > high:
            score -= penalty_per_metric     
    return max(0, score)

def sanitize_metrics(metrics):
    """กันค่าแปลกปลอมก่อนลง Database"""
    sanitized = {}
    for k, v in metrics.items():
        if np.isnan(v) or np.isinf(v):
            sanitized[k] = 0.0
        else:
            sanitized[k] = float(np.clip(v, -360, 360))
    return sanitized

#  Thresholds from Research
SUPINE_THRESHOLDS = {"NeckTilt": (0, 15), "TrunkFlex": (0, 20), "LatTilt": (-15, 15)}
PRONE_THRESHOLDS = {"HeadRot": (-30, 30), "NeckFlex": (0, 20), "AxialRot": (0, 20)}
SIDE_THRESHOLDS = {"BodyTilt": (25, 35), "NeckTilt": (0, 15), "AxialRot": (0, 15)}

#  Utility: Smooth Metrics
def smooth_metrics(metrics, posture_type):
    q = SMOOTH_QUEUE[posture_type]
    q.append(metrics)
    avg = {k: np.mean([m[k] for m in q]) for k in metrics}
    return avg

#  Pose Analysis Functions
def analyze_supine(lm, mp_pose=None, frame_shape=None):
    """นอนหงาย | CVA surrogate, TrunkFlex, LateralTilt (Raad 2022; Lee 2018; Nordin 2020)"""
    if not lm or len(lm) < 25:
        return "Invalid", {}, 0
    pts = normalize_landmark(lm, frame_shape)
    if pts is None: return "Invalid", {}, 0
    try:
        ls, rs = pts[11], pts[12]
        lh, rh = pts[23], pts[24]
        nose = pts[0]
    except Exception:
        return "Invalid", {}, 0
    shoulder_mid = (ls + rs) / 2
    hip_mid = (lh + rh) / 2
    neck_vec = nose - shoulder_mid
    trunk_vec = hip_mid - shoulder_mid
    neck_trunk_angle = vector_angle(neck_vec, trunk_vec)
    neck_tilt = abs(180 - neck_trunk_angle)
    trunk_flex = vector_angle(trunk_vec, [0, -1])
    lateral_tilt = np.degrees(np.arctan2(ls[1] - rs[1], rs[0] - ls[0]))
    metrics = {"NeckTilt": neck_tilt, "TrunkFlex": trunk_flex, "LatTilt": lateral_tilt}
    metrics = smooth_metrics(metrics, "supine")
    # reuse posture_score function for consistency
    score = posture_score(metrics, SUPINE_THRESHOLDS)
    quality = get_quality_label(score)
    db_metrics = {f"{METRIC_DB_MAP[k]}": v for k, v in metrics.items() if k in METRIC_DB_MAP}
    db_metrics = sanitize_metrics(db_metrics)
    return quality, db_metrics, score

def analyze_prone(lm, mp_pose=None, frame_shape=None):
    """นอนคว่ำ | HeadRot, NeckFlex, AxialRot (Kim 2015; Levangie & Norkin 2011; Dankaerts 2006)"""
    if not lm or lm[0].visibility < 0.5: # If nose is not visible, likely occluded in prone
        pass
    if not lm or len(lm) < 25:
        return "Invalid", {}, 0
    pts = normalize_landmark(lm, frame_shape)
    if pts is None: return "Invalid", {}, 0
    try:
        ls, rs = pts[11], pts[12]
        lh, rh = pts[23], pts[24]
        nose = pts[0]
    except Exception:
        return "Invalid", {}, 0
    shoulder_mid = (ls + rs) / 2
    hip_mid = (lh + rh) / 2
    head_vec = nose - shoulder_mid
    trunk_vec = hip_mid - shoulder_mid
    head_rot = wrap_angle(np.degrees(np.arctan2(head_vec[1], head_vec[0])))
    neck_flex = vector_angle(head_vec, trunk_vec)
    shoulder_angle = np.degrees(np.arctan2(ls[1] - rs[1], ls[0] - rs[0]))
    hip_angle = np.degrees(np.arctan2(lh[1] - rh[1], lh[0] - rh[0]))
    axial_rot = abs(wrap_angle(shoulder_angle - hip_angle))
    metrics = {"HeadRot": head_rot, "NeckFlex": neck_flex, "AxialRot": axial_rot}
    metrics = smooth_metrics(metrics, "prone")
    # reuse posture_score function for consistency
    score = posture_score(metrics, PRONE_THRESHOLDS)
    quality = get_quality_label(score)
    db_metrics = {f"{METRIC_DB_MAP[k]}": v for k, v in metrics.items() if k in METRIC_DB_MAP}
    db_metrics = sanitize_metrics(db_metrics)
    return quality, db_metrics, score

def analyze_side(lm, side="left", mp_pose=None, frame_shape=None):
    """นอนตะแคง | BodyTilt, NeckTilt, AxialRot (Li 2017; Davis 2020; Raad 2022)"""
    if not lm or len(lm) < 25:
        return "Invalid", {}, 0
    pts = normalize_landmark(lm, frame_shape)
    if pts is None: return "Invalid", {}, 0
    try:
        ls, rs = pts[11], pts[12]
        lh, rh = pts[23], pts[24]
        nose = pts[0]
    except Exception:
        return "Invalid", {}, 0
    shoulder_mid = (ls + rs) / 2
    hip_mid = (lh + rh) / 2
    trunk_vec = hip_mid - shoulder_mid
    neck_vec = nose - shoulder_mid
    body_tilt = vector_angle(trunk_vec, [0, -1])
    neck_tilt = vector_angle(neck_vec, trunk_vec)
    shoulder_angle = np.degrees(np.arctan2(ls[1] - rs[1], ls[0] - rs[0]))
    hip_angle = np.degrees(np.arctan2(lh[1] - rh[1], lh[0] - rh[0]))
    axial_rot = abs(wrap_angle(shoulder_angle - hip_angle))
    metrics = {"BodyTilt": body_tilt, "NeckTilt": neck_tilt, "AxialRot": axial_rot}
    metrics = smooth_metrics(metrics, "side")
    # reuse posture_score function for consistency
    score = posture_score(metrics, SIDE_THRESHOLDS)
    quality = get_quality_label(score)
    db_metrics = {f"{METRIC_DB_MAP[k]}": v for k, v in metrics.items() if k in METRIC_DB_MAP}
    db_metrics = sanitize_metrics(db_metrics)
    return quality, db_metrics, score