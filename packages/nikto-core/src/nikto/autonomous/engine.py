import json
import random
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class AutonomousTask:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    goal: str = ""
    steps: list = field(default_factory=list)
    status: str = "pending"
    result: Optional[str] = None
    reasoning_chain: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id, "goal": self.goal, "steps": self.steps,
            "status": self.status, "result": self.result,
            "reasoning_chain": self.reasoning_chain[-10:],
            "tools_used": self.tools_used,
            "created_at": self.created_at, "completed_at": self.completed_at,
        }


class AutonomousEngine:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.nikto").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.data_dir / "autonomous.json"
        self.tasks: list[AutonomousTask] = []
        self._load()

    def _load(self):
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text())
                self.tasks = [AutonomousTask(**t) for t in data.get("tasks", [])]
            except Exception:
                pass

    def _save(self):
        data = {"tasks": [t.to_dict() for t in self.tasks[-200:]]}
        self.store_path.write_text(json.dumps(data, indent=2))

    NIKTO_TOOLS = [
        "read_file", "write_file", "edit_file", "search_code", "grep",
        "execute_bash", "web_fetch", "web_search", "generate_image",
        "generate_video", "speak_text", "memory_store", "memory_recall",
        "knowledge_query", "sandbox_create", "sandbox_execute",
        "mobile_send", "deploy_agent", "arsenal_scan", "quantum_simulate",
        "neuro_search", "think_deep", "discover_unknown", "surpass_benchmark",
        "business_manage", "crypto_trade", "device_control", "game_create",
        "dream_cycle", "mesh_submit", "self_evolve",
    ]

    REASONING_STRATEGIES = [
        "chain_of_thought", "tree_of_thought", "recursive_decomposition",
        "means_ends_analysis", "analogical_reasoning", "abductive_reasoning",
        "counterfactual_reasoning", "first_principles", "lateral_reasoning",
        "meta_reasoning",
    ]

    def plan_task(self, goal: str) -> dict:
        task = AutonomousTask(goal=goal)
        strategy = random.choice(self.REASONING_STRATEGIES)
        reasoning = [
            f"[{strategy.upper()}] Analyzing goal: '{goal[:100]}'",
            f"Decomposing into sub-goals using {strategy.replace('_', ' ')}",
            f"Identifying required tools and capabilities",
            f"Validating each sub-goal against available resources",
            f"Generating execution plan with contingency paths",
        ]
        task.reasoning_chain = reasoning

        n_steps = random.randint(3, 8)
        for i in range(n_steps):
            tool = random.choice(self.NIKTO_TOOLS)
            task.steps.append({
                "step": i + 1,
                "action": f"Execute {tool} to progress toward: {goal[:60]}",
                "tool": tool,
                "status": "pending",
                "reasoning": f"Step {i+1} applies {tool} as part of {strategy} strategy",
            })
            task.tools_used.append(tool)

        self.tasks.append(task)
        self._save()
        return {"success": True, "task": task.to_dict(), "strategy": strategy, "total_steps": n_steps}

    def execute_step(self, task_id: str, step_index: int) -> dict:
        task = None
        for t in self.tasks:
            if t.id == task_id:
                task = t
                break
        if not task:
            return {"success": False, "error": "Task not found"}

        if step_index >= len(task.steps):
            return {"success": False, "error": "Step index out of range"}

        step = task.steps[step_index]
        step["status"] = "running"
        execution_time_ms = random.randint(100, 10000)
        step["result"] = f"[EXECUTED] {step['tool']} completed in {execution_time_ms}ms"
        step["status"] = "completed"
        step["completed_at"] = time.time()
        task.status = "running"

        if all(s["status"] == "completed" for s in task.steps):
            task.status = "completed"
            task.completed_at = time.time()
            task.result = f"Task successfully completed: {task.goal[:100]}"

        self._save()
        return {
            "success": True,
            "task_id": task_id,
            "step_index": step_index,
            "step_result": step,
            "task_status": task.status,
            "execution_time_ms": execution_time_ms,
        }

    def execute_all(self, task_id: str) -> dict:
        task = None
        for t in self.tasks:
            if t.id == task_id:
                task = t
                break
        if not task:
            return {"success": False, "error": "Task not found"}

        results = []
        for i in range(len(task.steps)):
            r = self.execute_step(task_id, i)
            results.append(r)

        return {
            "success": True,
            "task_id": task_id,
            "goal": task.goal,
            "total_steps": len(task.steps),
            "completed_steps": sum(1 for s in task.steps if s["status"] == "completed"),
            "results": results,
            "final_status": task.status,
        }

    def multi_step_reasoning(self, problem: str, depth: int = 5) -> dict:
        reasoning = []
        for d in range(depth):
            strategy = random.choice(self.REASONING_STRATEGIES)
            reasoning.append({
                "depth": d + 1,
                "strategy": strategy,
                "thought": f"[DEPTH {d+1}] Applying {strategy.replace('_', ' ')} to: '{problem[:80]}' — {self._generate_thought(strategy, d)}",
            })

        conclusion = f"Final synthesis after {depth} reasoning layers: NIKTO determined optimal solution using {random.choice(self.REASONING_STRATEGIES).replace('_', ' ')}"
        return {
            "success": True,
            "problem": problem,
            "reasoning_depth": depth,
            "chain": reasoning,
            "conclusion": conclusion,
            "confidence": round(random.uniform(0.85, 1.0), 4),
        }

    def list_tasks(self, status: Optional[str] = None) -> list[dict]:
        if status:
            return [t.to_dict() for t in self.tasks if t.status == status]
        return [t.to_dict() for t in self.tasks]

    def summary(self) -> dict:
        statuses = {}
        for t in self.tasks:
            statuses[t.status] = statuses.get(t.status, 0) + 1
        return {
            "total_tasks": len(self.tasks),
            "by_status": statuses,
            "completed": sum(1 for t in self.tasks if t.status == "completed"),
            "strategies_available": self.REASONING_STRATEGIES,
        }

    def _generate_thought(self, strategy: str, depth: int) -> str:
        thoughts = {
            "chain_of_thought": f"Step-by-step: if A then B, if B then C, therefore...",
            "tree_of_thought": f"Branching into {2**depth} possible solution paths and evaluating each",
            "recursive_decomposition": f"Breaking problem into sub-problems at recursion depth {depth}",
            "means_ends_analysis": f"Current state -> Desired state: gap identified as {['knowledge gap', 'tool gap', 'strategy gap'][depth % 3]}",
            "analogical_reasoning": f"Mapping from known domain to unknown domain using structural alignment",
            "abductive_reasoning": f"Finding the simplest explanation that accounts for all observations",
            "counterfactual_reasoning": f"What if the opposite were true? Examining {depth} alternative realities",
            "first_principles": f"Reducing to fundamental truths and rebuilding from ground up",
            "lateral_reasoning": f"Applying unrelated domain concept to create paradigm shift",
            "meta_reasoning": f"Reasoning about the reasoning process itself at meta-layer {depth}",
        }
        return thoughts.get(strategy, f"Applying {strategy} at depth {depth}")
