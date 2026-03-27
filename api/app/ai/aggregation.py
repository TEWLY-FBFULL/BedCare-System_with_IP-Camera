import time
import threading
from app.services.config_cache import ConfigCache

buffer_lock = threading.Lock()
aggregation_buffers = {}

class AggregationBuffer:
    def __init__(self, interval=None, max_frames=600):
        self.interval = int(interval or ConfigCache.get("sleep_log_interval_sec", 300))
        self.start_time = time.time()
        self.frames = []
        self.max_frames = max_frames 
        self._lock = threading.Lock()

    def add(self, data):
        with self._lock:
            if len(self.frames) < self.max_frames:
                self.frames.append(data)

    def ready(self):
        return time.time() - self.start_time >= self.interval

    def aggregate(self):
        with self._lock:
            if not self.frames:
                return None
            result = {"posture": [], "metrics": []}
            for f in self.frames:
                if "posture" in f: result["posture"].append(f["posture"])
                if "metrics" in f: result["metrics"].append(f["metrics"])
            self.frames = []
            self.start_time = time.time()
            return result