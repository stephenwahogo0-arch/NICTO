"""NIKTO Autopilot Engine — automated task execution with dependency resolution."""

import json
import asyncio
import hashlib
import uuid
import time
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict


class AutomationTask:
    def __init__(self, name: str, script: str, trigger: str = "manual",
                 interval_seconds: int = 3600, timeout: int = 300,
                 tags: list = None, metadata: dict = None):
        self.id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]
        self.name = name
        self.script = script
        self.trigger = trigger  # manual, interval, startup, event
        self.interval_seconds = interval_seconds
        self.timeout = timeout
        self.tags = tags or []
        self.metadata = metadata or {}
        self.status = "idle"
        self.last_run = None
        self.next_run = None
        self.run_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_output = None
        self.last_error = None
        self.created = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoAutopilot:
    """
    Autopilot Engine.
    Automates recurring tasks, runs scripts, manages automation routines.
    """

    SAFE_COMMANDS = {
        "nmap", "ping", "curl", "wget", "python", "python3",
        "powershell", "cmd", "dir", "ls", "cat", "echo", "whoami",
        "ipconfig", "ifconfig", "netstat", "tasklist", "ps",
    }

    def __init__(self):
        self.tasks = {}
        self.max_tasks = 200
        self._running = False
        self._loop_task = None
        self.execution_log = []
        self.max_log = 500

    # ── Task Management ───────────────────────────────────────────────

    def add_task(self, name: str, script: str, trigger: str = "manual",
                 interval_seconds: int = 3600, timeout: int = 300,
                 tags: list = None, metadata: dict = None) -> str:
        task = AutomationTask(name, script, trigger, interval_seconds,
                              timeout, tags, metadata)
        self.tasks[task.id] = task
        if len(self.tasks) > self.max_tasks:
            oldest = min(self.tasks.keys(),
                        key=lambda k: self.tasks[k].created)
            del self.tasks[oldest]
        return task.id

    def remove_task(self, task_id: str):
        self.tasks.pop(task_id, None)

    def get_task(self, task_id: str) -> Optional[dict]:
        task = self.tasks.get(task_id)
        return task.to_dict() if task else None

    def list_tasks(self, trigger: str = None, status: str = None) -> list:
        tasks = self.tasks.values()
        if trigger:
            tasks = [t for t in tasks if t.trigger == trigger]
        if status:
            tasks = [t for t in tasks if t.status == status]
        return [t.to_dict() for t in tasks]

    # ── Execution ─────────────────────────────────────────────────────

    async def run_task(self, task_id: str) -> dict:
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        task.status = "running"
        task.run_count += 1
        start = time.time()
        try:
            output = await self._execute_script(task.script, task.timeout)
            task.status = "idle"
            task.success_count += 1
            task.last_output = output[:1000]
            task.last_error = None
            result = {"success": True, "output": output[:1000]}
        except Exception as e:
            task.status = "idle"
            task.failure_count += 1
            task.last_error = str(e)
            result = {"success": False, "error": str(e)}
        elapsed = time.time() - start
        task.last_run = datetime.now(timezone.utc).isoformat()
        log_entry = {
            "task_id": task.id,
            "task_name": task.name,
            "success": result["success"],
            "elapsed": round(elapsed, 3),
            "timestamp": task.last_run,
        }
        self.execution_log.append(log_entry)
        if len(self.execution_log) > self.max_log:
            self.execution_log = self.execution_log[-self.max_log:]
        return result

    async def run_all_tasks(self, trigger: str = None) -> list:
        tasks = self.list_tasks(trigger=trigger) if trigger else self.list_tasks()
        results = []
        for t in tasks:
            result = await self.run_task(t["id"])
            results.append({"task_name": t["name"], **result})
        return results

    async def run_by_tag(self, tag: str) -> list:
        results = []
        for task in self.tasks.values():
            if tag in task.tags:
                result = await self.run_task(task.id)
                results.append({"task_name": task.name, **result})
        return results

    async def _execute_script(self, script: str, timeout: int) -> str:
        """Execute a script string safely."""
        if not script.strip():
            return "Empty script"
        lines = [l.strip() for l in script.strip().split("\n") if l.strip()]
        output_parts = []
        for line in lines:
            if line.startswith("#"):
                continue
            try:
                proc = await asyncio.create_subprocess_shell(
                    line,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
                out = stdout.decode(errors="replace").strip()
                err = stderr.decode(errors="replace").strip()
                parts = [f"$ {line}"]
                if out:
                    parts.append(out[:500])
                if err:
                    parts.append(f"[stderr] {err[:200]}")
                output_parts.append("\n".join(parts))
            except asyncio.TimeoutError:
                output_parts.append(f"$ {line}\n[TIMEOUT after {timeout}s]")
            except Exception as e:
                output_parts.append(f"$ {line}\n[ERROR: {e}]")
        return "\n".join(output_parts)

    # ── Scheduled Loop ────────────────────────────────────────────────

    async def start_autopilot(self):
        self._running = True
        self._loop_task = asyncio.create_task(self._autopilot_loop())
        return self

    async def stop_autopilot(self):
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()

    async def _autopilot_loop(self):
        while self._running:
            now = time.time()
            for task in self.tasks.values():
                if task.trigger != "interval":
                    continue
                if task.next_run is None:
                    task.next_run = now + task.interval_seconds
                elif now >= task.next_run:
                    await self.run_task(task.id)
                    task.next_run = now + task.interval_seconds
            await asyncio.sleep(30)

    # ── Statistics ────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        total = len(self.tasks)
        total_runs = sum(t.run_count for t in self.tasks.values())
        total_success = sum(t.success_count for t in self.tasks.values())
        total_failures = sum(t.failure_count for t in self.tasks.values())
        return {
            "total_tasks": total,
            "interval_tasks": len(self.list_tasks(trigger="interval")),
            "manual_tasks": len(self.list_tasks(trigger="manual")),
            "startup_tasks": len(self.list_tasks(trigger="startup")),
            "total_runs": total_runs,
            "total_success": total_success,
            "total_failures": total_failures,
            "success_rate": round(total_success / max(total_runs, 1) * 100, 1),
            "log_entries": len(self.execution_log),
        }

    def save(self) -> dict:
        return {
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "execution_log": self.execution_log[-100:],
        }

    def load(self, data: dict):
        self.tasks = {}
        for tid, td in data.get("tasks", {}).items():
            t = AutomationTask(td.get("name", tid), td.get("script", ""),
                               td.get("trigger", "manual"))
            t.__dict__.update(td)
            self.tasks[tid] = t
        self.execution_log = data.get("execution_log", [])
