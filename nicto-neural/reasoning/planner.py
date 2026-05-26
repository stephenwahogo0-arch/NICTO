"""Task planner — task decomposition and subgoal DAG."""

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class SubGoal:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    description: str = ""
    dependencies: list = field(default_factory=list)
    completed: bool = False
    priority: float = 0.5


class TaskPlanner:
    """Decomposes tasks into subgoal DAGs."""

    def __init__(self):
        self._plans: dict[str, list[SubGoal]] = {}

    def decompose(self, task: str, max_steps: int = 10) -> list[SubGoal]:
        """Break task into ordered subgoals."""
        words = task.lower().split()
        steps = []

        steps.append(SubGoal(description=f"Understand: {task[:80]}", priority=1.0))

        if any(k in task.lower() for k in ["build", "create", "implement"]):
            steps.append(SubGoal(description="Design architecture", priority=0.9))
            steps.append(SubGoal(
                description="Implement core logic",
                dependencies=[steps[-1].id],
                priority=0.8,
            ))
            steps.append(SubGoal(
                description="Test implementation",
                dependencies=[steps[-1].id],
                priority=0.7,
            ))
        elif any(k in task.lower() for k in ["analyze", "explain", "review"]):
            steps.append(SubGoal(description="Gather relevant data", priority=0.9))
            steps.append(SubGoal(
                description="Perform analysis",
                dependencies=[steps[-1].id],
                priority=0.8,
            ))
            steps.append(SubGoal(
                description="Synthesize findings",
                dependencies=[steps[-1].id],
                priority=0.7,
            ))
        else:
            steps.append(SubGoal(description="Research approach", priority=0.9))
            steps.append(SubGoal(
                description="Execute plan",
                dependencies=[steps[-1].id],
                priority=0.8,
            ))

        steps.append(SubGoal(
            description="Verify output quality",
            dependencies=[steps[-1].id],
            priority=0.6,
        ))

        plan_id = str(uuid4())[:8]
        self._plans[plan_id] = steps[:max_steps]
        return steps[:max_steps]

    def mark_complete(self, plan_id: str, subgoal_id: str) -> bool:
        if plan_id not in self._plans:
            return False
        for sg in self._plans[plan_id]:
            if sg.id == subgoal_id:
                sg.completed = True
                return True
        return False

    def get_next_actions(self, plan_id: str) -> list[SubGoal]:
        """Get subgoals whose dependencies are all completed."""
        if plan_id not in self._plans:
            return []
        completed_ids = {sg.id for sg in self._plans[plan_id] if sg.completed}
        return [
            sg for sg in self._plans[plan_id]
            if not sg.completed
            and all(dep in completed_ids for dep in sg.dependencies)
        ]

    def progress(self, plan_id: str) -> float:
        if plan_id not in self._plans:
            return 0.0
        plan = self._plans[plan_id]
        if not plan:
            return 1.0
        return sum(1 for sg in plan if sg.completed) / len(plan)
