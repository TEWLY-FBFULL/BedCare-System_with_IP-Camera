from ultralytics import YOLO
import torch

device = torch.device("cpu")
person_model = YOLO("./app/ai/models/yolov8s.pt").to(device)

def detect_person(frame):
    try:
        results = person_model.predict(
            source=frame,
            conf=0.3,
            classes=[0],
            imgsz=320, 
            verbose=False,
            device=device
        )
        if results and len(results[0].boxes) > 0:
            print(f"Detected person with conf {results[0].boxes[0].conf.item()}")
            return True
        return False
    except Exception as e:
        print(f"Error occurred: {e}")
        return False