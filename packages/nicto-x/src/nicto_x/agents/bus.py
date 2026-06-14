"""NICTO X — Agent message bus for inter-agent communication."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("nicto_x.bus")


@dataclass
class AgentMessage:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    sender: str = ""
    recipient: str = ""
    subject: str = ""
    body: dict = field(default_factory=dict)
    priority: int = 5
    timestamp: float = field(default_factory=time.time)
    reply_to: Optional[str] = None


class AgentBus:
    """Async message bus for agent-to-agent communication."""

    def __init__(self):
        self._queues: dict[str, asyncio.Queue] = {}
        self._history: list[AgentMessage] = []
        self._max_history = 1000

    def register(self, agent_name: str):
        if agent_name not in self._queues:
            self._queues[agent_name] = asyncio.Queue()

    async def send(self, message: AgentMessage):
        if message.recipient and message.recipient in self._queues:
            await self._queues[message.recipient].put(message)
        elif message.recipient == "*":
            for name, queue in self._queues.items():
                if name != message.sender:
                    m = AgentMessage(
                        sender=message.sender,
                        recipient=name,
                        subject=message.subject,
                        body=message.body,
                        priority=message.priority,
                    )
                    await queue.put(m)
        self._history.append(message)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    async def receive(self, agent_name: str, timeout: float = 1.0) -> Optional[AgentMessage]:
        queue = self._queues.get(agent_name)
        if not queue:
            return None
        try:
            return await asyncio.wait_for(queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    def get_history(self, limit: int = 50) -> list[AgentMessage]:
        return self._history[-limit:]

    async def broadcast(self, sender: str, subject: str, body: dict):
        await self.send(AgentMessage(sender=sender, recipient="*", subject=subject, body=body))
