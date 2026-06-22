"""Real capability scanner — actually detects available system capabilities."""
import importlib
import os
import shutil
import subprocess
import sys
from typing import Optional


class CapabilityScanner:
    def __init__(self):
        self.capabilities = {}

    def scan_all(self) -> dict:
        self.capabilities = {
            "python_version": sys.version,
            "platform": sys.platform,
            "cpus": os.cpu_count(),
            "modules": self._scan_modules(),
            "commands": self._scan_commands(),
            "hardware": self._scan_hardware(),
        }
        return self.capabilities

    def _scan_modules(self) -> dict:
        modules = ["numpy", "torch", "tensorflow", "transformers", "faiss", "pygame", "flask",
                    "fastapi", "requests", "paramiko", "docker", "kubernetes", "psutil", "PIL"]
        return {m: importlib.util.find_spec(m) is not None for m in modules}

    def _scan_commands(self) -> dict:
        commands = ["git", "docker", "kubectl", "ssh", "python3", "node", "npm", "gcc", "ffmpeg"]
        return {c: shutil.which(c) is not None for c in commands}

    def _scan_hardware(self) -> dict:
        info = {}
        try:
            import psutil
            info["memory_gb"] = round(psutil.virtual_memory().total / 1e9, 1)
            info["disk_gb"] = round(psutil.disk_usage("/").free / 1e9, 1)
            info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        except ImportError:
            info["memory_gb"] = "unknown (install psutil)"
            info["disk_gb"] = "unknown"
        try:
            import torch
            info["cuda_available"] = torch.cuda.is_available()
            info["cuda_devices"] = torch.cuda.device_count() if torch.cuda.is_available() else 0
        except ImportError:
            info["cuda_available"] = False
        return info

    def get_summary(self) -> dict:
        if not self.capabilities:
            self.scan_all()
        return self.capabilities
