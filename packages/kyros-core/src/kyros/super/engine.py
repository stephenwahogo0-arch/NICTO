"""Real super engine — tracks actual capability improvements."""
import json
import os
import time
from pathlib import Path
from typing import Optional


CAPABILITIES = ["reasoning", "coding", "planning", "memory", "creativity", "analysis", "synthesis", "evaluation"]


class SuperEngine:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or os.path.join(str(Path.home()), ".nikto", "super"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.data_dir / "state.json"
        self.super_score = 0.0
        self.capabilities = {c: 0.5 for c in CAPABILITIES}
        self.level = 1
        self._load()

    def _load(self):
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                self.super_score = data.get("super_score", 0.0)
                self.capabilities = data.get("capabilities", {})
                self.level = data.get("level", 1)
            except Exception:
                pass

    def _save(self):
        self.state_file.write_text(json.dumps({"super_score": self.super_score, "capabilities": self.capabilities, "level": self.level, "updated": time.time()}))

    def update_capability(self, name: str, score: float):
        if name in self.capabilities:
            old = self.capabilities[name]
            self.capabilities[name] = round(max(0, min(1, old + (score - old) * 0.1)), 4)
            self.super_score = round(sum(self.capabilities.values()) / len(self.capabilities), 4)
            if self.super_score > self.level * 0.1:
                self.level = min(20, int(self.super_score * 10) + 1)
            self._save()

    def get_state(self) -> dict:
        return {"super_score": self.super_score, "capabilities": self.capabilities, "level": self.level}
