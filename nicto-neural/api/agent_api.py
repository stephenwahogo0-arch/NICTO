"""Agent API — TaskOrchestrator.run() wrapper."""


class AgentAPI:
    """Public API for task orchestration."""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    async def run_task(self, task: str, context: dict = None) -> dict:
        return await self.orchestrator.run(task, context)

    def queue_task(self, task: str, priority: float = 0.5) -> dict:
        return self.orchestrator.queue_task(task, priority)

    async def process_queue(self, max_tasks: int = 10) -> list[dict]:
        return await self.orchestrator.process_queue(max_tasks)

    def get_stats(self) -> dict:
        return self.orchestrator.get_stats()
