from typing import Any, Dict, List, Optional
from .agents import BaseAgent, AgentResult
from .tools import ToolRegistry


class AgentOrchestrator:
    def __init__(self, agents: Dict[str, BaseAgent], tools: ToolRegistry):
        self.agents = agents
        self.tools = tools

    def run_task(self, task: Dict, mode: str = "parallel") -> Any:
        if mode == "parallel":
            return self._run_parallel(task)
        elif mode == "sequential":
            return self._run_sequential(task)
        elif mode == "best":
            return self._run_best(task)
        else:
            return self._run_parallel(task)

    def _run_parallel(self, task: Dict) -> List[AgentResult]:
        results = []
        for name, agent in self.agents.items():
            try:
                result = agent.run(task, self.tools)
                results.append(result)
            except Exception as e:
                results.append(AgentResult(agent=name, success=False, output=None))
        return results

    def _run_sequential(self, task: Dict) -> List[AgentResult]:
        results = []
        for name, agent in self.agents.items():
            try:
                result = agent.run(task, self.tools)
                results.append(result)
                if result.success and result.output:
                    task["context"] = result.output
            except Exception as e:
                results.append(AgentResult(agent=name, success=False, output=None))
        return results

    def _run_best(self, task: Dict) -> AgentResult:
        domain = task.get("domain", "general")
        preferred = {
            "code": "code",
            "research": "research",
            "plan": "planner",
            "memory": "memory",
            "evaluate": "evaluation",
            "execute": "execution",
        }
        agent_name = preferred.get(domain, "research")
        agent = self.agents.get(agent_name)
        if agent is None:
            agent = list(self.agents.values())[0]
        return agent.run(task, self.tools)

    def merge_results(self, results: List[Any], strategy: str = "consensus") -> Any:
        if not results:
            return None
        if strategy == "consensus":
            values = [r.output if hasattr(r, "output") else r for r in results]
            return values
        elif strategy == "best":
            scored = [(r.confidence if hasattr(r, "confidence") else 0.5, r.output if hasattr(r, "output") else r) for r in results]
            scored.sort(key=lambda x: x[0], reverse=True)
            return scored[0][1]
        return results

    def detect_conflicts(self, results: List[Any]) -> List[Dict]:
        conflicts = []
        for i, r1 in enumerate(results):
            for j, r2 in enumerate(results):
                if i >= j:
                    continue
                o1 = r1.output if hasattr(r1, "output") else str(r1)
                o2 = r2.output if hasattr(r2, "output") else str(r2)
                if o1 and o2 and o1[:50] != o2[:50]:
                    conflicts.append({
                        "agent_a": r1.agent if hasattr(r1, "agent") else i,
                        "agent_b": r2.agent if hasattr(r2, "agent") else j,
                        "description": f"Conflict between outputs"
                    })
        return conflicts