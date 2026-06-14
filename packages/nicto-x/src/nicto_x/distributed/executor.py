"""NICTO X — Distributed execution layer with worker pools, task queues, and horizontal scaling."""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger("nicto_x.distributed")


@dataclass
class Task:
    id: str = field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    name: str = ""
    payload: dict = field(default_factory=dict)
    priority: int = 5
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class WorkerResult:
    worker_id: str
    task_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0


class WorkQueue:
    """Priority-based async work queue with task tracking."""

    def __init__(self):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks: dict[str, Task] = {}
        self._completed: list[Task] = []
        self._max_completed = 1000

    async def enqueue(self, task: Task):
        priority = max(0, min(10, task.priority))
        await self._queue.put((priority, task))
        self._tasks[task.id] = task

    async def dequeue(self) -> Optional[Task]:
        try:
            _, task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            task.status = "running"
            task.started_at = time.time()
            return task
        except asyncio.TimeoutError:
            return None

    async def complete(self, task: Task, result: Any = None, error: Optional[str] = None):
        if error:
            task.status = "failed"
            task.error = error
        else:
            task.status = "completed"
            task.result = result
        task.completed_at = time.time()
        self._completed.append(task)
        if len(self._completed) > self._max_completed:
            self._completed = self._completed[-self._max_completed:]

    def get_pending_count(self) -> int:
        return self._queue.qsize()

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def get_status(self) -> dict:
        return {
            "pending": self._queue.qsize(),
            "completed": len(self._completed),
            "total_tracked": len(self._tasks),
        }


class TaskWorker:
    """Worker that processes tasks from a queue."""

    def __init__(self, worker_id: str, queue: WorkQueue, handler: Optional[Callable] = None):
        self.worker_id = worker_id
        self.queue = queue
        self.handler = handler
        self._running = False
        self._tasks_processed = 0
        self._total_duration_ms = 0.0

    async def run(self):
        self._running = True
        while self._running:
            task = await self.queue.dequeue()
            if task:
                start = time.time()
                try:
                    if self.handler:
                        result = await self.handler(task.payload)
                    else:
                        result = f"Processed by worker {self.worker_id}"
                    await self.queue.complete(task, result=result)
                except Exception as e:
                    await self.queue.complete(task, error=str(e))
                elapsed = (time.time() - start) * 1000
                self._tasks_processed += 1
                self._total_duration_ms += elapsed
            else:
                await asyncio.sleep(0.1)

    def stop(self):
        self._running = False

    def get_stats(self) -> dict:
        return {
            "worker_id": self.worker_id,
            "tasks_processed": self._tasks_processed,
            "avg_duration_ms": round(self._total_duration_ms / max(self._tasks_processed, 1), 2),
        }


class DistributedExecutor:
    """Manages worker pools, distributes tasks, and scales horizontally."""

    def __init__(self, min_workers: int = 2, max_workers: int = 8):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.queue = WorkQueue()
        self._workers: dict[str, TaskWorker] = {}
        self._tasks: asyncio.Task[None] | None = None
        self._running = False

    async def start(self):
        self._running = True
        for i in range(self.min_workers):
            wid = f"worker_{i}"
            worker = TaskWorker(wid, self.queue)
            self._workers[wid] = worker

        self._tasks = asyncio.create_task(self._run_workers())
        logger.info("Distributed executor started with %d workers", len(self._workers))

    async def _run_workers(self):
        tasks = [asyncio.create_task(w.run()) for w in self._workers.values()]
        await asyncio.gather(*tasks)

    async def submit(self, name: str, payload: dict, priority: int = 5) -> str:
        task = Task(name=name, payload=payload, priority=priority)
        await self.queue.enqueue(task)
        return task.id

    async def submit_batch(self, tasks: list[tuple[str, dict, int]]) -> list[str]:
        ids = []
        for name, payload, priority in tasks:
            task_id = await self.submit(name, payload, priority)
            ids.append(task_id)
        return ids

    async def scale_up(self, count: int = 1):
        for i in range(count):
            wid = f"worker_{len(self._workers)}"
            worker = TaskWorker(wid, self.queue)
            self._workers[wid] = worker
            if self._running:
                asyncio.create_task(worker.run())
        logger.info("Scaled up to %d workers", len(self._workers))

    async def scale_down(self, count: int = 1):
        to_remove = list(self._workers.keys())[:count]
        for wid in to_remove:
            self._workers[wid].stop()
            del self._workers[wid]
        logger.info("Scaled down to %d workers", len(self._workers))

    async def stop(self):
        for w in self._workers.values():
            w.stop()
        self._running = False
        if self._tasks:
            self._tasks.cancel()
        logger.info("Distributed executor stopped")

    def get_status(self) -> dict:
        return {
            "running": self._running,
            "workers": {wid: w.get_stats() for wid, w in self._workers.items()},
            "queue": self.queue.get_status(),
            "scale": f"{len(self._workers)}/{self.max_workers}",
        }

    def get_result(self, task_id: str) -> Optional[dict]:
        task = self.queue.get_task(task_id)
        if task:
            return {"id": task.id, "name": task.name, "status": task.status, "result": task.result, "error": task.error, "created_at": task.created_at, "completed_at": task.completed_at}
        return None
