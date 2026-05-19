"""Autopilot Engine — runs background profit-generation loop."""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from nikto.autopilot.connections import ConnectionManager
from nikto.autopilot.finance import FinanceManager
from nikto.autopilot.tasks import AutopilotTask, TaskPriority, TaskResult
from nikto.business.engine import BusinessEngine

logger = logging.getLogger(__name__)


class AutopilotStatus(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class AutopilotConfig:
    interval_seconds: int = 60
    data_dir: str = "~/.nikto/autopilot"
    max_concurrent_tasks: int = 5
    auto_connect: bool = True
    notify_on_earnings: bool = True
    earnings_threshold_usd: float = 1.0


class AutopilotEngine:
    """Background autopilot that runs profit-generating tasks autonomously."""

    def __init__(self, config: Optional[AutopilotConfig] = None):
        self.config = config or AutopilotConfig()
        self.status = AutopilotStatus.STOPPED
        self.session_id = str(uuid.uuid4())
        self._task = None
        self._loop_running = False
        self.connections = ConnectionManager()
        self.finance = FinanceManager(data_dir=self.config.data_dir)
        self.business = BusinessEngine(data_dir=self.config.data_dir)
        self.completed_tasks: list[TaskResult] = []
        self.total_earnings: float = 0.0
        self.start_time: Optional[datetime] = None
        self._task_registry: dict[str, AutopilotTask] = {}
        self._pending_tasks: list[AutopilotTask] = []
        self._active_tasks: dict[str, asyncio.Task] = {}

    def register_task(self, task: AutopilotTask):
        self._task_registry[task.name] = task

    def unregister_task(self, name: str):
        self._task_registry.pop(name, None)

    def list_tasks(self) -> list[str]:
        return list(self._task_registry.keys())

    async def start(self):
        if self.status == AutopilotStatus.RUNNING:
            return
        self.status = AutopilotStatus.RUNNING
        self.start_time = datetime.now()
        self._loop_running = True

        if self.config.auto_connect:
            await self.connections.auto_discover()

        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Autopilot started (session={self.session_id})")

    async def stop(self):
        self._loop_running = False
        self.status = AutopilotStatus.STOPPED
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        for t in self._active_tasks.values():
            t.cancel()
        self._active_tasks.clear()
        self.connections.disconnect_all()
        await self.finance.save()
        logger.info("Autopilot stopped")

    async def pause(self):
        self.status = AutopilotStatus.PAUSED
        self._loop_running = False
        for t in self._active_tasks.values():
            t.cancel()
        self._active_tasks.clear()

    async def resume(self):
        self.status = AutopilotStatus.RUNNING
        self._loop_running = True
        self._task = asyncio.create_task(self._run_loop())

    async def _run_loop(self):
        while self._loop_running:
            try:
                # Auto-launch capital-free businesses if none exist
                if len(self.business.list_businesses()) == 0:
                    for btype in ["content", "service", "digital", "affiliate", "micro"]:
                        result = self.business.start_business(btype)
                        if result["success"]:
                            logger.info(f"Autopilot auto-launched {btype} business: {result['business']['id']}")

                # Scan for available tasks
                ready_tasks = self._select_ready_tasks()
                for task in ready_tasks:
                    if len(self._active_tasks) >= self.config.max_concurrent_tasks:
                        break
                    at = asyncio.create_task(self._execute_task(task))
                    self._active_tasks[task.name] = at

                # Check completed active tasks
                done = [n for n, t in self._active_tasks.items() if t.done()]
                for n in done:
                    self._active_tasks.pop(n, None)

                # Update finance projections
                await self.finance.refresh_balances()

                await asyncio.sleep(self.config.interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Autopilot loop error: {e}")
                self.status = AutopilotStatus.ERROR
                await asyncio.sleep(5)

        self.status = AutopilotStatus.STOPPED

    def _select_ready_tasks(self) -> list[AutopilotTask]:
        now = time.time()
        ready = []
        still_pending = []
        for task in self._pending_tasks:
            if task.next_run_at <= now:
                ready.append(task)
            else:
                still_pending.append(task)
        self._pending_tasks = still_pending
        for task in self._task_registry.values():
            if task not in ready and task.enabled:
                ready.append(task)
                task.next_run_at = time.time() + task.interval
                self._pending_tasks.append(task)
        return ready[:self.config.max_concurrent_tasks]

    async def _execute_task(self, task: AutopilotTask) -> TaskResult:
        try:
            result = await task.execute(self.connections, self.finance)
            result.session_id = self.session_id
            self.completed_tasks.append(result)
            if result.earnings > 0:
                self.total_earnings += result.earnings
                await self.finance.record_earnings(result)
                if self.config.notify_on_earnings and result.earnings >= self.config.earnings_threshold_usd:
                    channels = self.finance.get_notification_channels()
                    await self.finance.send_earnings_notification(result, channels)
            return result
        except Exception as e:
            logger.error(f"Task {task.name} failed: {e}")
            return TaskResult(task_name=task.name, success=False, error=str(e))

    def status_report(self) -> dict:
        recent = self.completed_tasks[-20:] if self.completed_tasks else []
        biz_summary = self.business.summary()
        return {
            "status": self.status.value,
            "session_id": self.session_id,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            "total_earnings": self.total_earnings,
            "tasks_completed": len(self.completed_tasks),
            "tasks_succeeded": sum(1 for t in self.completed_tasks if t.success),
            "tasks_failed": sum(1 for t in self.completed_tasks if not t.success),
            "active_tasks": len(self._active_tasks),
            "registered_tasks": len(self._task_registry),
            "pending_tasks": len(self._pending_tasks),
            "connections": self.connections.count(),
            "recent_tasks": [t.to_dict() for t in recent],
            "wallets": self.finance.get_wallet_summaries(),
            "businesses": biz_summary,
        }
