from ultralytics import YOLO
import torch
import os
import cv2
import numpy as np

os.environ["LD_LIBRARY_PATH"] = os.environ.get("LD_LIBRARY_PATH", "") + ":/usr/local/cuda/lib64"
device = "0" if torch.cuda.is_available() else "cpu"

if torch.cuda.is_available():
    print(f"AI Core: Using GPU ({torch.cuda.get_device_name(0)})")
else:
    print("AI Core: Running on CPU")
try:
    posture_model = YOLO("./app/ai/models/best.onnx")
    print(f"✅ Model loaded. Classes: {posture_model.names}")
except Exception as e:
    print(f"Failed to load model: {e}")
    posture_model = None

def classify_posture(frame):
    if posture_model is None or frame is None:
        return None
    try:
        h, w = frame.shape[:2]
        input_frame = cv2.resize(frame, (640, 640)) if (h != 640 or w != 640) else frame
        
        results = posture_model.predict(
            input_frame,
            imgsz=640, 
            conf=0.3,
            verbose=False,
            device=device
        )
        
        if not results or len(results[0].boxes) == 0:
            return None
        
        top_box = results[0].boxes[0]
        
        class_idx = int(top_box.cls.item()) 
        confidence = float(top_box.conf.item()) 
        
        model_names = posture_model.names 
        label_name = model_names.get(class_idx)

        if label_name is None:
            print(f"❌ Unknown class index: {class_idx}")
            return None
            
        if confidence < 0.3:
            return None
        
        print(f"✅ Classified (Detection Mode): {label_name} ({confidence:.2f})")
        return label_name, confidence
    
    except Exception as e:
        print(f"⚠️ Posture Classifier Error: {e}")
        return None