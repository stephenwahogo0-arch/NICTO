"""Task orchestration — autonomous end-to-end pipeline. NICTO thinks, not delegates."""


class TaskOrchestrator:
    """Autonomous task pipeline — NICTO processes tasks with its own brain."""

    def __init__(self, consciousness, tool_registry, safety_policies):
        self.consciousness = consciousness
        self.tools = tool_registry
        self.policies = safety_policies
        self._task_queue: list[dict] = []
        self._completed: list[dict] = []

    async def run(self, task: str, context: dict = None) -> dict:
        """Full pipeline: think -> plan -> execute -> reflect."""
        rate_check = self.policies.check_rate_limit("think")
        if not rate_check["allowed"]:
            return {"error": rate_check["reason"], "status": "rate_limited"}

        result = await self.consciousness.think(task, context or {})

        return {
            "task": task[:100],
            "result": result,
            "status": "completed",
            "think_count": self.consciousness._think_count,
        }

    def queue_task(self, task: str, priority: float = 0.5) -> dict:
        entry = {
            "task": task,
            "priority": priority,
            "status": "queued",
        }
        self._task_queue.append(entry)
        self._task_queue.sort(key=lambda t: t["priority"], reverse=True)
        return entry

    async def process_queue(self, max_tasks: int = 10) -> list[dict]:
        """Process queued tasks in priority order."""
        results = []
        for _ in range(min(max_tasks, len(self._task_queue))):
            if not self._task_queue:
                break
            task_entry = self._task_queue.pop(0)
            result = await self.run(task_entry["task"])
            task_entry["status"] = "completed"
            task_entry["result"] = result
            results.append(task_entry)
            self._completed.append(task_entry)
        return results

    def get_stats(self) -> dict:
        return {
            "queued": len(self._task_queue),
            "completed": len(self._completed),
        }
