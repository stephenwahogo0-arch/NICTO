from typing import Any, Dict, List, Optional
from ..execution.agents import BaseAgent
from ..execution.tools import ToolRegistry
from ..execution.orchestration import AgentOrchestrator


class AgentAPI:
    def __init__(self, agents: Dict[str, BaseAgent] = None, tools: ToolRegistry = None):
        self._orchestrator = None
        if agents and tools:
            self._orchestrator = AgentOrchestrator(agents, tools)

    def run_task(self, task: Dict, mode: str = "parallel") -> Any:
        if self._orchestrator is None:
            return {"error": "AgentOrchestrator not initialized"}
        return self._orchestrator.run_task(task, mode)

    def list_agents(self) -> List[str]:
        if self._orchestrator is None:
            return []
        return list(self._orchestrator.agents.keys())

    def agent_status(self, agent_name: str = None) -> Dict:
        if self._orchestrator is None:
            return {"initialized": False}
        names = [agent_name] if agent_name else list(self._orchestrator.agents.keys())
        return {name: {"available": True} for name in names}

    def set_orchestrator(self, orchestrator):
        self._orchestrator = orchestrator