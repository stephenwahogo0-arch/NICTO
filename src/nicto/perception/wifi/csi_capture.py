"""Cross-platform Wi-Fi CSI (Channel State Information) capture."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Callable
from dataclasses import dataclass, field
import platform
import time
import random
import math


@dataclass
class CSIFrame:
    timestamp: float = 0.0
    source_mac: str = "00:00:00:00:00:00"
    csi_matrix: list[list[complex]] = field(default_factory=list)
    snr_db: float = 30.0
    noise_floor: float = -90.0
    bandwidth_mhz: int = 80
    num_subcarriers: int = 256


class CSICaptureBackend(ABC):
    @abstractmethod
    def start_capture(self, interface: str, callback: Callable[[CSIFrame], None]) -> bool:
        ...

    @abstractmethod
    def stop_capture(self) -> bool:
        ...

    @abstractmethod
    def get_supported_interfaces(self) -> list[str]:
        ...


class LinuxCSICapture(CSICaptureBackend):
    def start_capture(self, interface: str, callback: Callable) -> bool:
        raise RuntimeError("Install: pip install nicto-core[wifi] (requires pylibnl)")

    def stop_capture(self) -> bool:
        return True

    def get_supported_interfaces(self) -> list[str]:
        return ["wlan0", "wlp2s0"]


class WindowsCSICapture(CSICaptureBackend):
    def start_capture(self, interface: str, callback: Callable) -> bool:
        raise RuntimeError("Windows CSI requires NDIS driver support")

    def stop_capture(self) -> bool:
        return True

    def get_supported_interfaces(self) -> list[str]:
        return ["Wi-Fi", "Ethernet"]


class macOSCSICapture(CSICaptureBackend):
    def start_capture(self, interface: str, callback: Callable) -> bool:
        raise RuntimeError("Install: pip install nicto-core[wifi] (requires pyobjc)")

    def stop_capture(self) -> bool:
        return True

    def get_supported_interfaces(self) -> list[str]:
        return ["en0"]


class SyntheticCSIGenerator(CSICaptureBackend):
    """Generates realistic fake CSI data for development/testing."""

    def __init__(self):
        self._running = False
        self._thread = None

    def start_capture(self, interface: str, callback: Callable) -> bool:
        self._running = True
        import threading
        def _gen():
            t = 0.0
            while self._running:
                n_sub = 256
                gesture_phase = math.sin(t * 0.5) * math.pi
                csi = [[complex(math.cos(gesture_phase + i * 0.1),
                                math.sin(gesture_phase + i * 0.1 + random.gauss(0, 0.05)))
                        for i in range(n_sub)]]
                frame = CSIFrame(
                    timestamp=time.time(),
                    source_mac="00:1a:2b:3c:4d:5e",
                    csi_matrix=csi,
                    snr_db=30 + random.gauss(0, 2),
                    num_subcarriers=n_sub,
                )
                try:
                    callback(frame)
                except Exception:
                    pass
                time.sleep(0.05)
                t += 0.05
        self._thread = threading.Thread(target=_gen, daemon=True)
        self._thread.start()
        return True

    def stop_capture(self) -> bool:
        self._running = False
        return True

    def get_supported_interfaces(self) -> list[str]:
        return ["synthetic0"]


VALID_GESTURES = [
    "swipe_left", "swipe_right", "swipe_up", "swipe_down",
    "push", "pull", "rotate_clockwise", "rotate_counter",
    "tap", "double_tap", "hold",
]


class CrossPlatformCSI:
    """Factory + fallback manager for CSI capture."""

    @staticmethod
    def create_backend() -> CSICaptureBackend:
        system = platform.system()
        backends = {
            "Linux": LinuxCSICapture,
            "Windows": WindowsCSICapture,
            "Darwin": macOSCSICapture,
        }
        cls = backends.get(system)
        if cls:
            try:
                return cls()
            except Exception:
                pass
        return CrossPlatformCSI.get_synthetic_backend()

    @staticmethod
    def get_synthetic_backend() -> SyntheticCSIGenerator:
        return SyntheticCSIGenerator()


class GestureRecognizer:
    """Classifies Wi-Fi CSI data into gestures using a simple model."""

    def __init__(self):
        self.csi = CrossPlatformCSI.create_backend()
        self._callbacks: list[Callable] = []

    def on_gesture(self, callback: Callable[[str, float], None]):
        self._callbacks.append(callback)

    def _classify(self, frame: CSIFrame) -> tuple[str, float]:
        if not frame.csi_matrix:
            return "unknown", 0.0
        magnitudes = [abs(c) for row in frame.csi_matrix for c in row]
        if not magnitudes:
            return "unknown", 0.0
        avg = sum(magnitudes) / len(magnitudes)
        variance = sum((m - avg) ** 2 for m in magnitudes) / len(magnitudes)
        if variance > 0.1:
            return "swipe_left" if sum(magnitudes[:len(magnitudes)//2]) > sum(magnitudes[len(magnitudes)//2:]) else "swipe_right", min(0.95, variance)
        return "tap", 0.85

    def start(self, interface: str = "auto"):
        if interface == "auto":
            ifaces = self.csi.get_supported_interfaces()
            interface = ifaces[0] if ifaces else "synthetic0"
        def _handler(frame: CSIFrame):
            gesture, confidence = self._classify(frame)
            if gesture != "unknown":
                for cb in self._callbacks:
                    try:
                        cb(gesture, confidence)
                    except Exception:
                        pass
        self.csi.start_capture(interface, _handler)

    def stop(self):
        self.csi.stop_capture()
