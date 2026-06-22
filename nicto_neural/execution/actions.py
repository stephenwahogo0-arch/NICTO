import os
import subprocess
import tempfile
from typing import Any, Dict
from dataclasses import dataclass


@dataclass
class ActionResult:
    success: bool
    data: Any
    error: str = ""


class ActionExecutor:
    def __init__(self, sandbox_dir: str = None):
        self.sandbox_dir = sandbox_dir or os.path.join(tempfile.gettempdir(), "nicto_sandbox")
        os.makedirs(self.sandbox_dir, exist_ok=True)

    def execute(self, action_type: str, params: Dict) -> ActionResult:
        handlers = {
            "read_file": self.read_file,
            "write_file": self.write_file,
            "run_shell": self.run_shell,
            "list_dir": self.list_dir,
            "delete_file": self.delete_file,
        }
        handler = handlers.get(action_type)
        if handler is None:
            return ActionResult(False, None, f"Unknown action: {action_type}")
        try:
            return handler(**params)
        except Exception as e:
            return ActionResult(False, None, str(e))

    def read_file(self, path: str) -> ActionResult:
        safe_path = self._safepath(path)
        if not os.path.exists(safe_path):
            return ActionResult(False, None, f"File not found: {path}")
        with open(safe_path, "r", encoding="utf-8", errors="replace") as f:
            data = f.read()
        return ActionResult(True, data)

    def write_file(self, path: str, content: str) -> ActionResult:
        safe_path = self._safepath(path)
        os.makedirs(os.path.dirname(os.path.abspath(safe_path)), exist_ok=True)
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)
        return ActionResult(True, len(content))

    def run_shell(self, command: str, timeout: int = 30) -> ActionResult:
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            return ActionResult(
                result.returncode == 0,
                result.stdout,
                result.stderr if result.returncode != 0 else "",
            )
        except subprocess.TimeoutExpired:
            return ActionResult(False, None, "Command timed out")

    def list_dir(self, path: str = ".") -> ActionResult:
        safe_path = self._safepath(path)
        if not os.path.exists(safe_path):
            return ActionResult(False, None, f"Path not found: {path}")
        items = os.listdir(safe_path)
        return ActionResult(True, items)

    def delete_file(self, path: str) -> ActionResult:
        safe_path = self._safepath(path)
        if not os.path.exists(safe_path):
            return ActionResult(False, None, f"File not found: {path}")
        os.remove(safe_path)
        return ActionResult(True, f"Deleted: {path}")

    def _safepath(self, path: str) -> str:
        if os.path.isabs(path):
            return path
        return os.path.join(self.sandbox_dir, path)
