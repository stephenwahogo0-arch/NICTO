"""NICTO X — Planning agent with recursive decomposition, dependency management, and milestone tracking."""

from __future__ import annotations

import logging
import time
from typing import Any, Optional
from nicto_x.agents.base import BaseAgent

logger = logging.getLogger("nicto_x.agents.planning")


class PlanningAgent(BaseAgent):
    """Decomposes complex objectives into hierarchical task graphs with dependencies."""

    AGENT_MAP = {
        "research": ["research", "search", "find", "what is", "explain", "how does", "investigate", "study", "analyze", "compare", "literature", "review"],
        "coding": ["code", "build", "implement", "write", "program", "develop", "function", "class", "api", "server", "script", "app", "software"],
        "planning": ["plan", "strategy", "roadmap", "steps", "how to", "approach", "design", "architecture", "blueprint"],
        "security": ["security", "audit", "vulnerability", "threat", "hack", "exploit", "penetration", "firewall", "encrypt"],
        "vision": ["image", "picture", "photo", "vision", "ocr", "screenshot", "diagram", "chart", "visual", "video"],
        "memory": ["remember", "memory", "recall", "previous", "history", "context", "past", "store", "retrieve"],
        "evaluation": ["evaluate", "assess", "grade", "score", "review", "check", "validate", "verify", "test"],
    }

    async def create_plan(self, objective: str, context: Optional[dict] = None) -> dict:
        context = context or {}
        top_level = self._decompose(objective, depth=0)

        for step in top_level:
            if self._is_complex(step.get("task", "")):
                sub_steps = self._decompose(step["task"], depth=1)
                step["sub_steps"] = sub_steps

        dependencies = self._build_dependencies(top_level)
        milestones = self._create_milestones(top_level, objective)

        plan = {
            "objective": objective,
            "steps": top_level,
            "dependencies": dependencies,
            "milestones": milestones,
            "complexity": self._estimate_complexity(top_level),
            "estimated_steps": self._count_steps(top_level),
            "agent_assignments": self._extract_agents(top_level),
            "timestamp": time.time(),
        }
        return plan

    async def execute(self, task: str, context: Optional[dict] = None) -> dict:
        plan = await self.create_plan(task, context)
        summary = self._summarize(plan)
        return {"agent": self.name, "task": task, "output": summary, "plan": plan}

    def _decompose(self, objective: str, depth: int = 0) -> list:
        q = objective.lower()
        steps = []
        agents_used = set()

        for agent_name, keywords in self.AGENT_MAP.items():
            if any(kw in q for kw in keywords):
                task_desc = self._generate_task_desc(agent_name, objective)
                step = {
                    "id": f"step_{len(steps) + 1}_d{depth}",
                    "agent": agent_name,
                    "task": task_desc,
                    "order": len(steps) + 1,
                    "depth": depth,
                    "dependencies": [],
                    "sub_steps": [],
                }
                steps.append(step)
                agents_used.add(agent_name)

        if not steps:
            steps.append({
                "id": f"step_1_d{depth}",
                "agent": "research",
                "task": f"Analyze: {objective}",
                "order": 1,
                "depth": depth,
                "dependencies": [],
                "sub_steps": [],
            })
            steps.append({
                "id": f"step_2_d{depth}",
                "agent": "planning",
                "task": f"Plan: {objective}",
                "order": 2,
                "depth": depth,
                "dependencies": ["step_1_d{depth}"],
                "sub_steps": [],
            })
            agents_used.update(["research", "planning"])

        steps.append({
            "id": f"step_eval_d{depth}",
            "agent": "evaluation",
            "task": f"Evaluate: {objective}",
            "order": len(steps) + 1,
            "depth": depth,
            "dependencies": [s["id"] for s in steps],
            "sub_steps": [],
        })

        for i in range(1, len(steps)):
            if not steps[i]["dependencies"] and i > 0:
                prev_id = steps[i - 1]["id"]
                if prev_id != steps[i]["id"]:
                    steps[i]["dependencies"].append(prev_id)

        return steps

    def _generate_task_desc(self, agent: str, objective: str) -> str:
        descriptions = {
            "research": f"Research and gather information: {objective}",
            "coding": f"Develop code/implementation: {objective}",
            "planning": f"Design strategy and plan: {objective}",
            "security": f"Security analysis: {objective}",
            "vision": f"Visual analysis: {objective}",
            "memory": f"Memory operations: {objective}",
            "evaluation": f"Quality evaluation: {objective}",
        }
        return descriptions.get(agent, f"Process: {objective}")

    def _is_complex(self, task: str) -> bool:
        indicators = ["build", "develop", "implement", "create", "research", "analyze", "design"]
        return sum(1 for i in indicators if i in task.lower()) > 1 or len(task) > 100

    def _build_dependencies(self, steps: list) -> list:
        deps = []
        for step in steps:
            for dep_id in step.get("dependencies", []):
                deps.append({"from": dep_id, "to": step["id"]})
        return deps

    def _create_milestones(self, steps: list, objective: str) -> list:
        milestones = []
        if steps:
            milestones.append({"id": "ms_1", "description": f"Initial analysis of: {objective[:40]}", "steps": [steps[0]["id"]]})
        mid = len(steps) // 2
        if mid > 0 and mid < len(steps):
            milestones.append({"id": "ms_2", "description": "Mid-point progress check", "steps": [s["id"] for s in steps[:mid + 1]]})
        if steps:
            milestones.append({"id": "ms_3", "description": "Final review and delivery", "steps": [s["id"] for s in steps]})
        return milestones

    def _estimate_complexity(self, steps: list) -> str:
        total = self._count_steps(steps)
        if total > 10: return "very_high"
        if total > 6: return "high"
        if total > 3: return "medium"
        return "low"

    def _count_steps(self, steps: list) -> int:
        count = len(steps)
        for s in steps:
            count += len(s.get("sub_steps", []))
        return count

    def _extract_agents(self, steps: list) -> list:
        agents = set()
        for s in steps:
            agents.add(s.get("agent", "research"))
            for ss in s.get("sub_steps", []):
                agents.add(ss.get("agent", "research"))
        return sorted(agents)

    def _summarize(self, plan: dict) -> str:
        lines = [f"Plan: {plan['objective'][:80]}", f"Complexity: {plan['complexity']}", f"Steps: {plan['estimated_steps']}", f"Agents: {', '.join(plan['agent_assignments'])}"]
        for s in plan["steps"]:
            lines.append(f"  [{s['agent']}] {s['task'][:60]}")
        for m in plan["milestones"]:
            lines.append(f"  Milestone: {m['description']}")
        return "\n".join(lines)
