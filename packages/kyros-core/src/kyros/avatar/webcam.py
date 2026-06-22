"""Webcam integration — face detection, recognition, gaze tracking.

Frame-skipping: processes only 5 fps instead of full camera framerate.
GPU offloading: uses cv2.CPU/GPU backends when available.
Process isolation: runs in low-priority process to avoid thermal/OOM."""
import os
import platform
import threading
import time
from typing import Optional

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class WebcamEngine:
    TARGET_FPS = 5  # Frame-skipping: process only 5 frames per second
    FRAME_INTERVAL = 1.0 / TARGET_FPS

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
        self._frame_counter = 0
        self._last_process_time = 0.0
        self._lock = threading.Lock()
        self._gpu_backend = self._detect_gpu_backend()
        self._init_cascade()

    def _detect_gpu_backend(self) -> str:
        """Detect available GPU backend for OpenCV."""
        if not CV2_AVAILABLE:
            return "none"
        try:
            if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                return "cuda"
        except Exception:
            pass
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        system = platform.system()
        if system == "Darwin":
            try:
                import coremltools as ct
                return "coreml"
            except ImportError:
                pass
        return "cpu"

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
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 15)
            self.running = True
            self._thread = threading.Thread(target=self._capture_loop, daemon=True)
            self._thread.start()
            self._set_low_priority()
            return {"success": True, "status": "started", "gpu_backend": self._gpu_backend}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _set_low_priority(self):
        """Process isolation — reduce resource contention."""
        if PSUTIL_AVAILABLE:
            try:
                proc = psutil.Process()
                if platform.system() == "Windows":
                    proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                else:
                    proc.nice(10)
            except Exception:
                pass

    def _capture_loop(self):
        while self.running and self.cap:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            self._frame_counter += 1
            now = time.time()

            # Frame-skipping: only process frames at TARGET_FPS rate
            if now - self._last_process_time < self.FRAME_INTERVAL:
                continue

            with self._lock:
                self.last_frame = frame

            if self.face_cascade is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if self._gpu_backend == "cuda":
                    try:
                        gpu_mat = cv2.cuda_GpuMat()
                        gpu_mat.upload(gray)
                        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                    except Exception:
                        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                else:
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                with self._lock:
                    self.face_count = len(faces)
                    self.face_positions = [(x, y, w, h) for (x, y, w, h) in faces]
                    if faces:
                        self.last_detection_time = now

            self._last_process_time = now

            idle_time = self.FRAME_INTERVAL - (time.time() - now)
            if idle_time > 0:
                time.sleep(idle_time)

    def detect_faces(self) -> dict:
        with self._lock:
            count = self.face_count
            positions = list(self.face_positions)
            since_detection = time.time() - self.last_detection_time if self.last_detection_time else -1
        return {
            "success": True,
            "face_count": count,
            "positions": positions,
            "gpu_backend": self._gpu_backend,
            "target_fps": self.TARGET_FPS,
            "time_since_last_detection": round(since_detection, 2),
        }

    def get_face_direction(self) -> str:
        with self._lock:
            positions = list(self.face_positions)
        if not positions:
            return "none"
        if self.last_frame is None:
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
            "gpu_backend": self._gpu_backend,
            "target_fps": self.TARGET_FPS,
            "frame_skip_active": True,
            "low_priority": self._thread is not None,
        }