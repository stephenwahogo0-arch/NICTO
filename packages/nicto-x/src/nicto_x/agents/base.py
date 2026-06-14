"""NICTO X — Base agent class."""

from __future__ import annotations

import logging
from typing import Any, Optional

from nicto_x.agents.bus import AgentBus, AgentMessage
from nicto_x.core.config import NictoXConfig

logger = logging.getLogger("nicto_x.agents")


class BaseAgent:
    """Base class for all NICTO X agents."""

    def __init__(self, bus: AgentBus, config: NictoXConfig, name: str = ""):
        self.bus = bus
        self.config = config
        self.name = name or self.__class__.__name__.lower().replace("agent", "")
        self.bus.register(self.name)
        self._initialized = False

    async def initialize(self):
        self._initialized = True

    async def shutdown(self):
        self._initialized = False

    async def execute(self, task: Any, context: Optional[dict] = None) -> dict:
        raise NotImplementedError

    async def send_message(
        self, recipient: str, subject: str, body: dict, priority: int = 5
    ):
        await self.bus.send(
            AgentMessage(
                sender=self.name,
                recipient=recipient,
                subject=subject,
                body=body,
                priority=priority,
            )
        )

    async def receive_message(self, timeout: float = 1.0) -> Optional[AgentMessage]:
        return await self.bus.receive(self.name, timeout=timeout)
