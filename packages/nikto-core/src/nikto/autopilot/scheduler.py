import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Optional


class ScheduledTask:
    def __init__(self, name: str, cron_expr: str, description: str):
        self.name = name
        self.cron_expr = cron_expr
        self.description = description
        self.last_run = None
        self.next_run = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoScheduler:
    DEFAULT_SCHEDULE = [
        ScheduledTask("knowledge_consolidation", "0 3 * * *", "Consolidate and optimize knowledge base"),
        ScheduledTask("self_health_check", "*/30 * * * *", "Run health checks on all modules"),
        ScheduledTask("learning_review", "0 6 * * *", "Review and process queued learning tasks"),
        ScheduledTask("memory_cleanup", "0 2 * * 0", "Clean duplicate and stale memories"),
        ScheduledTask("performance_report", "0 9 * * 1", "Generate weekly performance report"),
        ScheduledTask("update_check", "0 12 * * *", "Check for NICTO updates on GitHub"),
        ScheduledTask("crypto_market_check", "*/15 * * * *", "Monitor crypto prices for wallet"),
        ScheduledTask("threat_intel_update", "0 */6 * * *", "Update threat intelligence feeds"),
    ]

    def __init__(self):
        self.tasks = {t.name: t for t in self.DEFAULT_SCHEDULE}
        self._running = False
        self._loop_task = None

    async def start(self):
        self._running = True
        self._loop_task = asyncio.create_task(self._scheduler_loop())
        return self

    async def stop(self):
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()

    async def _scheduler_loop(self):
        while self._running:
            now = datetime.now(timezone.utc)
            for task in self.tasks.values():
                if self._should_run(task, now):
                    task.last_run = now.isoformat()
            await asyncio.sleep(60)

    def _should_run(self, task: ScheduledTask, now: datetime) -> bool:
        if not task.last_run:
            return True
        parts = task.cron_expr.split()
        if len(parts) != 5:
            return False
        minute = parts[0]
        if minute == "*/30" and now.minute % 30 == 0:
            return True
        if minute == "*/15" and now.minute % 15 == 0:
            return True
        if minute == "0" and now.minute == 0:
            return True
        if minute == "*/6" and now.hour % 6 == 0 and now.minute == 0:
            return True
        return False

    def list_tasks(self) -> list:
        return [t.to_dict() for t in self.tasks.values()]

    def get_task(self, name: str) -> Optional[dict]:
        task = self.tasks.get(name)
        return task.to_dict() if task else None

    def add_task(self, name: str, cron_expr: str, description: str):
        self.tasks[name] = ScheduledTask(name, cron_expr, description)

    def remove_task(self, name: str):
        self.tasks.pop(name, None)
