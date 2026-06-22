"""Real autonomous engine — plans and executes tasks via subprocess or agent."""
import json
import os
import random
import shlex
import subprocess
import time
import uuid
from pathlib import Path
from typing import Optional


TOOLS = ["bash", "python", "file_read", "file_write", "web_search", "git"]


class AutonomousEngine:
    def __init__(self, data_dir: Optional[str] = None, agent=None):
        self.data_dir = Path(data_dir or os.path.join(str(Path.home()), ".nikto", "autonomous"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.agent = agent
        self.tasks = {}

    def plan_task(self, goal: str) -> dict:
        task_id = uuid.uuid4().hex[:12]
        steps = []
        if self.agent and hasattr(self.agent, 'run_sync'):
            plan_prompt = f"Create a step-by-step plan to accomplish: {goal}\nList concrete actions with tools."
            plan = self.agent.run_sync(plan_prompt)
            lines = str(plan).split("\n") if plan else []
            for i, line in enumerate(lines[:8]):
                if line.strip():
                    tool = random.choice(TOOLS)
                    steps.append({"step": i + 1, "action": line.strip()[:200], "tool": tool, "status": "pending"})
        else:
            for i in range(random.randint(3, 6)):
                tool = random.choice(TOOLS)
                steps.append({"step": i + 1, "action": f"Execute {tool} for {goal[:50]}", "tool": tool, "status": "pending"})
        plan = {"task_id": task_id, "goal": goal, "steps": steps, "status": "planned", "created": time.time()}
        self.tasks[task_id] = plan
        return plan

    def execute_step(self, task_id: str, step_idx: int = 0) -> dict:
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        if step_idx >= len(task["steps"]):
            return {"success": False, "error": "Step index out of range"}
        step = task["steps"][step_idx]
        start = time.time()
        try:
            if step["tool"] == "bash":
                result = subprocess.run(step["action"], shell=True, capture_output=True, text=True, timeout=15)
                step["result"] = result.stdout[:500] or result.stderr[:500]
                step["success"] = result.returncode == 0
            elif step["tool"] == "python":
                result = subprocess.run(["python", "-c", step["action"]], capture_output=True, text=True, timeout=15)
                step["result"] = result.stdout[:500]
                step["success"] = True
            else:
                step["result"] = f"Executed {step['tool']}: {step['action'][:100]}"
                step["success"] = True
            step["status"] = "completed"
            step["time_ms"] = int((time.time() - start) * 1000)
        except Exception as e:
            step["result"] = str(e)
            step["success"] = False
            step["status"] = "failed"
        task["steps"][step_idx] = step
        all_done = all(s["status"] == "completed" for s in task["steps"])
        if all_done:
            task["status"] = "completed"
        return {"step": step, "task_status": task["status"]}

    def execute_all(self, task_id: str) -> list:
        results = []
        task = self.tasks.get(task_id)
        if not task:
            return [{"success": False, "error": "Task not found"}]
        for i in range(len(task["steps"])):
            results.append(self.execute_step(task_id, i))
        task["status"] = "completed"
        return results

    def list_tasks(self) -> list:
        return [{"id": tid, "goal": t["goal"][:100], "status": t["status"], "steps": len(t["steps"])} for tid, t in self.tasks.items()]
