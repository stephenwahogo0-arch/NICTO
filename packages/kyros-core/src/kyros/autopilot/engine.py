from enum import Enum
from uuid import uuid4
from datetime import datetime


class AutopilotStatus(Enum):
    STOPPED = "stopped"
    RUNNING = "running"


class AutopilotConfig:
    def __init__(self, interval_seconds: int = 3600, max_tasks: int = 50):
        self.interval_seconds = interval_seconds
        self.max_tasks = max_tasks


class AutopilotEngine:
    def __init__(self, config: AutopilotConfig = None):
        self.config = config or AutopilotConfig()
        self.status = AutopilotStatus.STOPPED
        self.tasks = {}
        self.earnings = 0.0
        self.tasks_completed = 0

    def register_task(self, name: str, task_type: str, config: dict = None) -> dict:
        task_id = str(uuid4())[:12]
        self.tasks[task_id] = {"id": task_id, "name": name, "type": task_type, "config": config or {}, "created_at": datetime.now().isoformat()}
        return self.tasks[task_id]

    def list_tasks(self) -> list[dict]:
        return list(self.tasks.values())

    def start(self) -> dict:
        self.status = AutopilotStatus.RUNNING
        return {"success": True, "status": "running"}

    def stop(self) -> dict:
        self.status = AutopilotStatus.STOPPED
        return {"success": True, "status": "stopped"}

    def status_report(self) -> dict:
        return {"status": self.status.value, "earnings": self.earnings, "tasks_completed": self.tasks_completed, "total_tasks": len(self.tasks), "running": self.status == AutopilotStatus.RUNNING}
