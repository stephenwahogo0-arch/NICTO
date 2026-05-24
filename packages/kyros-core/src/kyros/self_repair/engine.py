"""Real self-repair engine — logs failures and suggests fixes."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


class CodeHealer:
    def heal(self, code: str, error: str = "") -> str:
        return code


class SelfRepairEngine:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or os.path.join(str(Path.home()), ".nikto", "self_repair"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.data_dir / "repair_log.json"
        self.failures = self._load()

    def _load(self) -> list:
        if self.log_file.exists():
            try:
                return json.loads(self.log_file.read_text())
            except Exception:
                pass
        return []

    def _save(self):
        self.log_file.write_text(json.dumps(self.failures[-500:], indent=2))

    def attempt_repair(self, module_name: str, error: str) -> dict:
        fixes = []
        if "ModuleNotFoundError" in error or "ImportError" in error:
            missing = error.split("'")[1] if "'" in error else module_name
            try:
                result = subprocess.run([sys.executable, "-m", "pip", "install", missing],
                                        capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    fixes.append({"type": "pip_install", "name": missing, "success": True})
                else:
                    fixes.append({"type": "pip_install", "name": missing, "success": False, "error": result.stderr[:200]})
            except Exception as e:
                fixes.append({"type": "pip_install_failed", "name": missing, "error": str(e)})
        if "AttributeError" in error:
            fixes.append({"type": "suggestion", "suggestion": f"Check attribute access in {module_name}"})
        entry = {"module": module_name, "error": error[:500], "fixes": fixes, "time": time.time()}
        self.failures.append(entry)
        self._save()
        return {"module": module_name, "error": error[:200], "fixes": fixes, "fixed": any(f.get("success") for f in fixes)}

    def get_log(self) -> list:
        return self.failures[-100:]
