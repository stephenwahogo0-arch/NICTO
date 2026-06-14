"""Base agent class and agent registry for the multi-agent game creation system."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Optional

from nicto_game.core.config import GameConfig


class GameAgent(ABC):
    """Base class for all AI game creation agents."""

    def __init__(self, name: str):
        self.name = name
        self.status = "idle"
        self.results: list[dict[str, Any]] = []

    @abstractmethod
    async def execute(self, task: dict[str, Any], config: GameConfig) -> dict[str, Any]:
        ...

    def report(self, result: dict[str, Any]):
        self.results.append(result)
        return result


class AgentCoordinator:
    """Coordinates collaboration between specialized agents."""

    def __init__(self):
        self.agents: dict[str, GameAgent] = {}

    def register(self, agent: GameAgent):
        self.agents[agent.name] = agent

    def get(self, name: str) -> Optional[GameAgent]:
        return self.agents.get(name)

    async def execute_pipeline(self, config: GameConfig) -> dict[str, Any]:
        results: dict[str, Any] = {}

        plan_task = {
            "type": "plan",
            "prompt": config.description,
            "genre": config.genre.value,
            "complexity": "high" if config.world.width > 100 else "medium",
        }

        pipeline = [
            ("planner", plan_task),
        ]

        for agent_name, task in pipeline:
            agent = self.agents.get(agent_name)
            if agent:
                agent.status = "running"
                try:
                    result = await agent.execute(task, config)
                    results[agent_name] = result
                except Exception as e:
                    results[agent_name] = {"error": str(e)}
                agent.status = "idle"

        return results
