from typing import Any, Dict, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from .tools import ToolRegistry


@dataclass
class AgentResult:
    agent: str
    success: bool
    output: Any
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)


class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.history: List[AgentResult] = []

    @abstractmethod
    def run(self, task: Dict, tools: ToolRegistry) -> AgentResult:
        pass


class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("research")

    def run(self, task: Dict, tools: ToolRegistry) -> AgentResult:
        query = task.get("input", "")
        result = tools.call("search_knowledge", query=query)
        return AgentResult(agent=self.name, success=True, output=result, confidence=0.8)


class CodeAgent(BaseAgent):
    def __init__(self):
        super().__init__("code")

    def run(self, task: Dict, tools: ToolRegistry) -> AgentResult:
        code = task.get("code", task.get("input", ""))
        result = tools.call("execute_code", code=code)
        return AgentResult(agent=self.name, success=True, output=result, confidence=0.9)


class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("planner")

    def run(self, task: Dict, tools: ToolRegistry) -> AgentResult:
        steps = task.get("steps", [task.get("input", "")])
        plan = {"task": task.get("input"), "steps": steps, "estimated_time": len(steps) * 2}
        return AgentResult(agent=self.name, success=True, output=plan, confidence=0.85)


class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__("memory")

    def run(self, task: Dict, tools: ToolRegistry) -> AgentResult:
        query = task.get("query", task.get("input", ""))
        limit = task.get("limit", 10)
        result = tools.call("query_memory", query=query, limit=limit)
        return AgentResult(agent=self.name, success=True, output=result, confidence=0.75)


class EvaluationAgent(BaseAgent):
    def __init__(self):
        super().__init__("evaluation")

    def run(self, task: Dict, tools: ToolRegistry) -> AgentResult:
        criteria = task.get("criteria", ["correctness", "completeness"])
        scores = {c: 0.8 for c in criteria}
        return AgentResult(agent=self.name, success=True, output=scores, confidence=0.7)


class ExecutionAgent(BaseAgent):
    def __init__(self):
        super().__init__("execution")

    def run(self, task: Dict, tools: ToolRegistry) -> AgentResult:
        commands = task.get("commands", [task.get("input", "")])
        results = []
        for cmd in commands:
            results.append(f"Executed: {cmd[:50]}")
        return AgentResult(agent=self.name, success=True, output=results, confidence=0.95)