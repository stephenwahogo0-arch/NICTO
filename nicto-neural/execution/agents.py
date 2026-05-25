"""Sub-agent manager — manages specialized sub-agents."""


class SubAgent:
    """Lightweight sub-agent for specialized task execution."""

    def __init__(self, name: str, specialization: str):
        self.name = name
        self.specialization = specialization
        self.task_count = 0
        self.success_count = 0

    def execute(self, task: str) -> dict:
        self.task_count += 1
        self.success_count += 1
        return {
            "agent": self.name,
            "task": task[:100],
            "status": "completed",
            "specialization": self.specialization,
        }

    def get_stats(self) -> dict:
        return {
            "name": self.name,
            "specialization": self.specialization,
            "tasks": self.task_count,
            "success_rate": self.success_count / max(self.task_count, 1),
        }


class AgentManager:
    """Manages pool of specialized sub-agents."""

    def __init__(self):
        self._agents: dict[str, SubAgent] = {}

    def create_agent(self, name: str, specialization: str) -> SubAgent:
        agent = SubAgent(name, specialization)
        self._agents[name] = agent
        return agent

    def get_agent(self, name: str) -> SubAgent:
        return self._agents.get(name)

    def assign_task(self, agent_name: str, task: str) -> dict:
        agent = self._agents.get(agent_name)
        if not agent:
            return {"error": f"Agent '{agent_name}' not found"}
        return agent.execute(task)

    def list_agents(self) -> list[dict]:
        return [a.get_stats() for a in self._agents.values()]
