"""NICTO X — Working memory: maintains active tasks, objectives, and reasoning chains."""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from nicto_x.core.config import MemoryConfig

logger = logging.getLogger("nicto_x.memory.working")


class WorkingMemory:
    """Short-term scratchpad for active context during reasoning."""

    def __init__(self, config: MemoryConfig):
        self.config = config
        self._slots: dict[str, Any] = {}
        self._history: list[dict] = []

    async def store(self, key: str, value: Any):
        self._slots[key] = {
            "value": value,
            "timestamp": time.time(),
        }
        if len(self._slots) > self.config.working_memory_size:
            oldest = min(self._slots.keys(), key=lambda k: self._slots[k]["timestamp"])
            del self._slots[oldest]

    async def retrieve(self, key: str) -> Optional[Any]:
        entry = self._slots.get(key)
        return entry["value"] if entry else None

    async def clear(self):
        self._history.append({"snapshot": dict(self._slots), "timestamp": time.time()})
        self._slots.clear()

    def get_context(self) -> dict[str, Any]:
        return {k: v["value"] for k, v in self._slots.items()}

    def get_recent_history(self, limit: int = 5) -> list[dict]:
        return self._history[-limit:]
