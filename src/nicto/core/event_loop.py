"""NICTO Event Loop — manages agent lifecycle and async execution."""
from __future__ import annotations
import asyncio
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class EventLoopConfig:
    tick_rate_hz: float = 60.0
    max_queue_size: int = 1000
    auto_start: bool = True


class EventLoop:
    """Main event loop for agent processing."""

    def __init__(self, config: Optional[EventLoopConfig] = None):
        self.config = config or EventLoopConfig()
        self._running = False
        self._tasks: list[asyncio.Task] = []
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=self.config.max_queue_size)

    def start(self):
        self._running = True

    def stop(self):
        self._running = False
        for t in self._tasks:
            t.cancel()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()
