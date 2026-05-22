"""Model Manager — multi-tier model download, auto-detection, and management.

Tier 1 (1B-3B): For 2GB RAM laptops — TinyLlama, Phi-2, Qwen2.5-1.5B
Tier 2 (7B-8B): For 16GB+ RAM laptops — Mistral-7B, Llama-3-8B
Tier 3 (Cloud): API-based — any remote model
"""

import json
import logging
import os
import platform
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# Model definitions: (name, huggingface_repo, filename, ram_min_gb, disk_gb)
MODEL_REGISTRY = {
    "tier1": [
        {
            "name": "Llama-3.2-1B",
            "repo": "hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF",
            "file": "llama-3.2-1b-instruct-q4_k_m.gguf",
            "ram_gb": 1.5,
            "disk_gb": 1.0,
            "description": "1B parameters — fits 2GB RAM laptops",
        },
        {
            "name": "Qwen2.5-1.5B",
            "repo": "Qwen/Qwen2.5-1.5B-Instruct-GGUF",
            "file": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
            "ram_gb": 1.8,
            "disk_gb": 1.2,
            "description": "1.5B parameters — good balance for low RAM",
        },
        {
            "name": "TinyLlama-1.1B",
            "repo": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
            "file": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
            "ram_gb": 1.2,
            "disk_gb": 0.7,
            "description": "1.1B — smallest viable model",
        },
    ],
    "tier2": [
        {
            "name": "Llama-3.2-3B",
            "repo": "hugging-quants/Llama-3.2-3B-Instruct-Q4_K_M-GGUF",
            "file": "llama-3.2-3b-instruct-q4_k_m.gguf",
            "ram_gb": 3.5,
            "disk_gb": 2.5,
            "description": "3B parameters — great for 8GB+ laptops",
        },
        {
            "name": "Mistral-7B",
            "repo": "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF",
            "file": "Mistral-7B-Instruct-v0.3.Q4_K_M.gguf",
            "ram_gb": 6.0,
            "disk_gb": 4.5,
            "description": "7B — powerful, needs 16GB RAM",
        },
        {
            "name": "Llama-3-8B",
            "repo": "hugging-quants/Llama-3-8B-Instruct-Q4_K_M-GGUF",
            "file": "Llama-3-8B-Instruct-Q4_K_M.gguf",
            "ram_gb": 6.5,
            "disk_gb": 5.0,
            "description": "8B — best quality, needs 16GB+ RAM",
        },
    ],
}


class ModelManager:
    """Manages model download, detection, and tier recommendation."""

    def __init__(self, models_dir: Optional[str] = None):
        self.models_dir = Path(models_dir or "~/.nikto/models").expanduser()
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.models_dir.parent / "model_config.json"
        self._config = self._load_config()

    def _load_config(self) -> dict:
        try:
            if self.config_file.exists():
                return json.loads(self.config_file.read_text())
        except Exception:
            pass
        return {"current_model": None, "tier": None}

    def _save_config(self):
        try:
            self.config_file.write_text(json.dumps(self._config, indent=2))
        except Exception:
            pass

    def detect_hardware_tier(self) -> str:
        """Auto-detect which tier this hardware supports."""
        try:
            if platform.system() == "Windows":
                import ctypes
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]
                mem = MEMORYSTATUSEX()
                mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
                ram_gb = mem.ullTotalPhys // (1024**3)
            else:
                import psutil
                ram_gb = psutil.virtual_memory().total // (1024**3)
        except Exception:
            ram_gb = 2

        # Check disk space
        try:
            disk_free = 0
            if platform.system() == "Windows":
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(str(self.models_dir)),
                    None, None, ctypes.byref(free_bytes)
                )
                disk_free = free_bytes.value // (1024**3)
            else:
                disk_free = 10  # Assume enough
        except Exception:
            disk_free = 10

        if ram_gb >= 16 and disk_free >= 8:
            return "tier2"  # Can run 7B-8B models
        elif ram_gb >= 4 and disk_free >= 2:
            return "tier1"  # Can run 1B-3B models
        else:
            return "tier1"  # Minimum viable

    def recommend_model(self) -> dict:
        """Recommend the best model for current hardware."""
        tier = self.detect_hardware_tier()
        models = MODEL_REGISTRY.get(tier, MODEL_REGISTRY["tier1"])
        # Pick the first (best) model in the tier
        return {"tier": tier, "model": models[0]}

    def list_installed(self) -> list[dict]:
        """List all installed GGUF models."""
        installed = []
        for f in self.models_dir.iterdir():
            if f.suffix in (".gguf", ".GGUF"):
                size_gb = f.stat().st_size / (1024**3) if f.exists() else 0
                installed.append({
                    "name": f.stem,
                    "path": str(f),
                    "size_gb": round(size_gb, 2),
                })
        return installed

    def download_model(self, model_key: str = "tier1") -> dict:
        """Download a model from HuggingFace."""
        tier = model_key if model_key in MODEL_REGISTRY else "tier1"
        models = MODEL_REGISTRY[tier]
        model_info = models[0]  # Pick first in tier

        repo = model_info["repo"]
        filename = model_info["file"]
        dest = self.models_dir / filename

        if dest.exists():
            return {"success": True, "path": str(dest), "already_exists": True}

        url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
        print(f"  Downloading {model_info['name']} ({model_info['disk_gb']} GB)...")
        print(f"  URL: {url}")
        print(f"  To: {dest}")
        print(f"  This may take a while depending on your internet speed.")

        try:
            urllib.request.urlretrieve(url, dest)
            self._config["current_model"] = str(dest)
            self._config["tier"] = tier
            self._save_config()
            return {"success": True, "path": str(dest), "already_exists": False}
        except Exception as e:
            return {"success": False, "error": str(e), "url": url, "dest": str(dest)}

    def get_current_model_path(self) -> Optional[str]:
        """Get path to currently configured model."""
        # Check config
        if self._config.get("current_model") and os.path.exists(self._config["current_model"]):
            return self._config["current_model"]
        # Find any installed model
        installed = self.list_installed()
        if installed:
            return installed[0]["path"]
        return None

    def print_status(self):
        """Print model status to console."""
        tier = self.detect_hardware_tier()
        installed = self.list_installed()
        print(f"\n  Hardware Tier: {tier}")
        print(f"  Models Directory: {self.models_dir}")
        print(f"  Installed Models: {len(installed)}")
        for m in installed:
            print(f"    - {m['name']} ({m['size_gb']} GB)")
        if not installed:
            print(f"    No models installed yet.")
            rec = self.recommend_model()
            print(f"  Recommended: {rec['model']['name']} ({rec['tier']})")
