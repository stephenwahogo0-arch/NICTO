"""Webcam integration — face detection, recognition, gaze tracking."""
import os
import threading
import time
from typing import Optional

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class WebcamEngine:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.running = False
        self.face_cascade = None
        self._thread = None
        self.last_frame = None
        self.face_count = 0
        self.face_positions = []
        self.last_detection_time = 0.0
        self._lock = threading.Lock()
        self._init_cascade()

    def _init_cascade(self):
        if not CV2_AVAILABLE:
            return
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        if os.path.exists(cascade_path):
            self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def start(self):
        if not CV2_AVAILABLE:
            return {"success": False, "error": "OpenCV not available"}
        if self.running:
            return {"success": True, "status": "already_running"}
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                return {"success": False, "error": "Cannot open camera"}
            self.running = True
            self._thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._thread.start()
            return {"success": True, "status": "started"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _capture_loop(self):
        while self.running and self.cap:
            ret, frame = self.cap.read()
            if not ret:
                continue
            with self._lock:
                self.last_frame = frame
            if self.face_cascade is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                with self._lock:
                    self.face_count = len(faces)
                    self.face_positions = [(x, y, w, h) for (x, y, w, h) in faces]
                    if faces:
                        self.last_detection_time = time.time()
            time.sleep(0.05)

    def detect_faces(self) -> dict:
        with self._lock:
            count = self.face_count
            positions = list(self.face_positions)
            since_detection = time.time() - self.last_detection_time if self.last_detection_time else -1
        return {
            "success": True,
            "face_count": count,
            "positions": positions,
            "time_since_last_detection": round(since_detection, 2),
        }

    def get_face_direction(self) -> str:
        with self._lock:
            positions = list(self.face_positions)
        if not positions:
            return "none"
        if not self.last_frame is not None:
            return "unknown"
        cx = self.last_frame.shape[1] // 2
        face_cx = positions[0][0] + positions[0][2] // 2
        diff = face_cx - cx
        if diff < -50:
            return "left"
        elif diff > 50:
            return "right"
        return "center"

    def capture_photo(self, path: str) -> dict:
        with self._lock:
            if self.last_frame is None:
                return {"success": False, "error": "No frame available"}
            frame = self.last_frame.copy()
        try:
            cv2.imwrite(path, frame)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
        return {"success": True}

    def summary(self) -> dict:
        return {
            "webcam_available": CV2_AVAILABLE,
            "running": self.running,
            "face_cascade_loaded": self.face_cascade is not None,
            "last_face_count": self.face_count,
        }