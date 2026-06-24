import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional
from nikto.brain.models import Goal, GoalStatus


class NiktoGoalSystem:

    def __init__(self):
        self.goals = {}
        self.goal_stack = []
        self.max_active_goals = 5

    def create_goal(self, description: str, priority: int = 5,
                    deadline: str = None, parent_id: str = None) -> str:
        goal = Goal(description=description, priority=priority, deadline=deadline)
        self.goals[goal.id] = goal
        if parent_id and parent_id in self.goals:
            self.goals[parent_id].subgoals.append(goal.id)
        self._reprioritize()
        return goal.id

    def create_subgoal(self, parent_id: str, description: str, priority: int = None) -> Optional[str]:
        if parent_id not in self.goals:
            return None
        parent = self.goals[parent_id]
        sub_priority = priority if priority is not None else parent.priority - 1
        return self.create_goal(description, sub_priority, parent_id=parent_id)

    def _reprioritize(self):
        active = [g for g in self.goals.values() if g.status == GoalStatus.ACTIVE]
        active.sort(key=lambda g: (-g.priority, g.created))

        if len(active) > self.max_active_goals:
            for g in active[self.max_active_goals:]:
                g.status = GoalStatus.PAUSED

    def get_active_goals(self) -> list:
        return [g.to_dict() for g in self.goals.values() if g.status == GoalStatus.ACTIVE]

    def get_next_goal(self) -> Optional[Goal]:
        active = [g for g in self.goals.values() if g.status == GoalStatus.ACTIVE]
        if not active:
            return None
        return max(active, key=lambda g: (g.priority, -g.progress))

    def update_progress(self, goal_id: str, amount: float):
        if goal_id in self.goals:
            self.goals[goal_id].update_progress(amount)
            if self.goals[goal_id].status == GoalStatus.COMPLETED:
                self._on_goal_complete(goal_id)

    def _on_goal_complete(self, goal_id: str):
        goal = self.goals[goal_id]
        for g in self.goals.values():
            if goal_id in g.subgoals:
                g.subgoals.remove(goal_id)
        self._reprioritize()

    def pause_goal(self, goal_id: str):
        if goal_id in self.goals:
            self.goals[goal_id].status = GoalStatus.PAUSED

    def resume_goal(self, goal_id: str):
        if goal_id in self.goals:
            self.goals[goal_id].status = GoalStatus.ACTIVE
            self._reprioritize()

    def abandon_goal(self, goal_id: str):
        if goal_id in self.goals:
            self.goals[goal_id].status = GoalStatus.ABANDONED
            self._reprioritize()

    def get_goal_chain(self, goal_id: str) -> list:
        chain = []
        current = self.goals.get(goal_id)
        while current:
            chain.insert(0, current.to_dict())
            parent_id = None
            for g in self.goals.values():
                if goal_id in g.subgoals:
                    parent_id = g.id
                    break
            goal_id = parent_id
            current = self.goals.get(goal_id) if goal_id else None
        return chain

    def evaluate_feasibility(self, goal_id: str) -> dict:
        if goal_id not in self.goals:
            return {"feasible": False, "reason": "goal_not_found"}
        goal = self.goals[goal_id]
        obstacles = []
        for g in self.goals.values():
            if g.id != goal_id and g.status == GoalStatus.ACTIVE and g.priority > goal.priority:
                obstacles.append(f"Higher priority goal: {g.description}")
        return {
            "feasible": len(obstacles) < 3,
            "priority": goal.priority,
            "progress": goal.progress,
            "obstacles": obstacles,
            "recommendation": "proceed" if len(obstacles) < 2 else "reassess",
        }

    def save(self) -> dict:
        return {
            "goals": {gid: g.to_dict() for gid, g in self.goals.items()},
            "goal_stack": list(self.goal_stack),
            "max_active_goals": self.max_active_goals,
        }

    def load(self, data: dict):
        self.max_active_goals = data.get("max_active_goals", 5)
        self.goal_stack = list(data.get("goal_stack", []))
        self.goals = {}
        for gid, gd in data.get("goals", {}).items():
            try:
                status = GoalStatus(gd.get("status", "active"))
            except ValueError:
                status = GoalStatus.ACTIVE
            goal = Goal(
                description=gd.get("description", ""),
                priority=gd.get("priority", 5),
                status=status,
                created=gd.get("created", datetime.now(timezone.utc).isoformat()),
                deadline=gd.get("deadline"),
                subgoals=list(gd.get("subgoals", [])),
                progress=gd.get("progress", 0.0),
                id=gd.get("id", gid),
                metadata=dict(gd.get("metadata", {})),
            )
            self.goals[gid] = goal

    def export(self) -> dict:
        return {gid: g.to_dict() for gid, g in self.goals.items()}
