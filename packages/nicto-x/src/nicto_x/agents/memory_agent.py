"""NICTO X — Memory agent for organizing, retrieving, and indexing knowledge."""

from __future__ import annotations

import logging
from typing import Any, Optional

from nicto_x.agents.base import BaseAgent
from nicto_x.memory.episodic import EpisodicMemory
from nicto_x.memory.semantic import SemanticMemory
from nicto_x.memory.consolidation import MemoryConsolidator

logger = logging.getLogger("nicto_x.agents.memory")


class MemoryAgent(BaseAgent):
    """Organizes memory, handles retrieval, and triggers consolidation."""

    def __init__(
        self,
        bus,
        config,
        episodic: Optional[EpisodicMemory] = None,
        semantic: Optional[SemanticMemory] = None,
    ):
        super().__init__(bus, config, name="memory")
        self.episodic = episodic or EpisodicMemory(config.memory)
        self.semantic = semantic or SemanticMemory(config.memory)
        self.consolidator = MemoryConsolidator(self.episodic, self.semantic)

    async def execute(self, task: Any, context: Optional[dict] = None) -> dict:
        task_str = str(task).lower()
        result: dict = {"agent": self.name}

        if "retrieve" in task_str or "recall" in task_str:
            results = await self.episodic.search(str(task), top_k=5)
            result["output"] = results
            result["action"] = "retrieved"
        elif "consolidate" in task_str:
            count = await self.consolidator.run()
            result["output"] = f"Consolidated {count} memories"
            result["action"] = "consolidated"
        elif "store" in task_str:
            if context and "episode" in context:
                await self.episodic.store(context["episode"])
                result["output"] = "Stored in episodic memory"
                result["action"] = "stored"
        else:
            result["output"] = f"Memory stats: {len(self.episodic)} episodic, {len(self.semantic)} semantic"
            result["action"] = "status"

        return result
