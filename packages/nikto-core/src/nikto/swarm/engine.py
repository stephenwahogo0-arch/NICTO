"""NIKTO Swarm Engine — Multi-agent coordination, task distribution, leader election."""

import json
import math
import random
import hashlib
import uuid
import time
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class SwarmAgent:
    def __init__(self, name: str, role: str, capabilities: list = None,
                 priority: int = 5, metadata: dict = None):
        self.id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]
        self.name = name
        self.role = role
        self.capabilities = capabilities or []
        self.priority = max(1, min(10, priority))
        self.status = "idle"  # idle, busy, error, offline
        self.load = 0.0
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.avg_response_time = 0.0
        self.last_heartbeat = datetime.now(timezone.utc).isoformat()
        self.metadata = metadata or {}
        self.current_task = None

    def capability_score(self, required: list) -> float:
        if not required:
            return 0.5
        matches = sum(1 for r in required if r in self.capabilities)
        return matches / len(required)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class SwarmTask:
    def __init__(self, name: str, description: str, required_capabilities: list = None,
                 priority: int = 5, metadata: dict = None):
        self.id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]
        self.name = name
        self.description = description
        self.required_capabilities = required_capabilities or []
        self.priority = max(1, min(10, priority))
        self.status = "pending"  # pending, assigned, in_progress, completed, failed
        self.assigned_to = None
        self.result = None
        self.created = datetime.now(timezone.utc).isoformat()
        self.completed_at = None
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoSwarmEngine:
    """
    Agent Swarming System.
    Coordinates multiple agents, assigns tasks, elects leaders,
    and merges results.
    """

    STRATEGIES = ["consensus", "hierarchical", "democratic",
                  "round_robin", "priority", "random"]

    def __init__(self, strategy: str = "consensus"):
        if strategy not in self.STRATEGIES:
            strategy = "consensus"
        self.strategy = strategy
        self.agents = {}  # id -> SwarmAgent
        self.tasks = {}  # id -> SwarmTask
        self.task_queue = []
        self.leader_id = None
        self._round_robin_idx = 0
        self.consensus_threshold = 0.6
        self.agent_timeout = 300.0  # 5 min without heartbeat = offline

    # ── Agent Management ──────────────────────────────────────────────

    def register_agent(self, name: str, role: str, capabilities: list = None,
                       priority: int = 5, metadata: dict = None) -> str:
        agent = SwarmAgent(name, role, capabilities, priority, metadata)
        self.agents[agent.id] = agent
        if self.leader_id is None:
            self.leader_id = agent.id
        return agent.id

    def remove_agent(self, agent_id: str):
        self.agents.pop(agent_id, None)
        if self.leader_id == agent_id:
            self._elect_leader()

    def get_agent(self, agent_id: str) -> Optional[dict]:
        agent = self.agents.get(agent_id)
        if agent:
            agent.last_heartbeat = datetime.now(timezone.utc).isoformat()
            return agent.to_dict()
        return None

    def list_agents(self, status: str = None) -> list:
        agents = self.agents.values()
        if status:
            agents = [a for a in agents if a.status == status]
        return [a.to_dict() for a in agents]

    def heartbeat(self, agent_id: str):
        agent = self.agents.get(agent_id)
        if agent:
            agent.last_heartbeat = datetime.now(timezone.utc).isoformat()

    def get_healthy_agents(self) -> list:
        now = datetime.now(timezone.utc)
        healthy = []
        for agent in self.agents.values():
            if agent.status == "offline":
                continue
            last = datetime.fromisoformat(agent.last_heartbeat)
            if (now - last).total_seconds() > self.agent_timeout:
                agent.status = "offline"
                continue
            healthy.append(agent)
        return healthy

    # ── Leader Election ───────────────────────────────────────────────

    def _elect_leader(self) -> Optional[str]:
        healthy = self.get_healthy_agents()
        if not healthy:
            self.leader_id = None
            return None

        if self.strategy == "hierarchical":
            # highest priority
            best = max(healthy, key=lambda a: a.priority)
            self.leader_id = best.id
        elif self.strategy == "democratic":
            # vote based on capability breadth
            total_caps = sum(len(a.capabilities) for a in healthy)
            if total_caps == 0:
                self.leader_id = healthy[0].id
            else:
                votes = defaultdict(float)
                for a in healthy:
                    for b in healthy:
                        if a.id != b.id:
                            score = len(b.capabilities) / max(total_caps, 1)
                            votes[a.id] += score
                self.leader_id = max(votes, key=votes.get)
        else:
            # consensus / default: highest capability score
            best = max(healthy, key=lambda a: (len(a.capabilities), a.priority))
            self.leader_id = best.id

        return self.leader_id

    def get_leader(self) -> Optional[dict]:
        if not self.leader_id or self.leader_id not in self.agents:
            self._elect_leader()
        agent = self.agents.get(self.leader_id)
        return agent.to_dict() if agent else None

    # ── Task Assignment ───────────────────────────────────────────────

    def submit_task(self, name: str, description: str,
                    required_capabilities: list = None,
                    priority: int = 5, metadata: dict = None) -> str:
        task = SwarmTask(name, description, required_capabilities, priority, metadata)
        self.tasks[task.id] = task
        self.task_queue.append(task.id)
        self.task_queue.sort(
            key=lambda tid: self.tasks[tid].priority,
            reverse=True,
        )
        return task.id

    def assign_next_task(self) -> Optional[dict]:
        if not self.task_queue:
            return None
        task_id = self.task_queue.pop(0)
        task = self.tasks[task_id]
        agent = self._select_agent(task)
        if not agent:
            task.status = "failed"
            return None
        task.assigned_to = agent.id
        task.status = "assigned"
        agent.status = "busy"
        agent.current_task = task.id
        return {"task": task.to_dict(), "agent": agent.to_dict()}

    def complete_task(self, task_id: str, result: any = None):
        task = self.tasks.get(task_id)
        if not task:
            return
        task.status = "completed"
        task.result = result
        task.completed_at = datetime.now(timezone.utc).isoformat()
        if task.assigned_to and task.assigned_to in self.agents:
            agent = self.agents[task.assigned_to]
            agent.status = "idle"
            agent.tasks_completed += 1
            agent.current_task = None

    def fail_task(self, task_id: str, error: str = None):
        task = self.tasks.get(task_id)
        if not task:
            return
        task.status = "failed"
        task.result = {"error": error}
        if task.assigned_to and task.assigned_to in self.agents:
            agent = self.agents[task.assigned_to]
            agent.status = "idle"
            agent.tasks_failed += 1
            agent.current_task = None

    def _select_agent(self, task: SwarmTask) -> Optional[SwarmAgent]:
        healthy = self.get_healthy_agents()
        available = [a for a in healthy if a.status == "idle"]
        if not available:
            available = healthy
        if not available:
            return None

        if self.strategy == "round_robin":
            idx = self._round_robin_idx % len(available)
            self._round_robin_idx = (idx + 1) % len(available)
            return available[idx]
        elif self.strategy == "random":
            return random.choice(available)
        elif self.strategy == "priority":
            return max(available, key=lambda a: a.priority)
        elif self.strategy in ("consensus", "democratic"):
            return max(available, key=lambda a: a.capability_score(task.required_capabilities))
        elif self.strategy == "hierarchical":
            return max(available, key=lambda a: a.priority)
        return available[0]

    # ── Result Merging ────────────────────────────────────────────────

    def merge_results(self, task_id: str, results: list) -> dict:
        """Merge multiple agent results for the same task."""
        if not results:
            return {"merged": False, "error": "No results to merge"}
        if len(results) == 1:
            return {"merged": True, "result": results[0], "method": "single"}

        if self.strategy == "consensus":
            return self._merge_consensus(results)
        elif self.strategy == "democratic":
            return self._merge_democratic(results)
        else:
            return self._merge_weighted(results)

    def _merge_consensus(self, results: list) -> dict:
        if not results:
            return {"merged": False, "error": "No results"}
        text_results = [r for r in results if isinstance(r, str)]
        if len(text_results) >= len(results) * self.consensus_threshold:
            from collections import Counter
            counter = Counter(text_results)
            most_common = counter.most_common(1)
            if most_common:
                return {"merged": True, "result": most_common[0][0],
                        "confidence": most_common[0][1] / max(len(text_results), 1),
                        "method": "consensus"}
        return {"merged": True, "result": results[0],
                "method": "first_among_equals"}

    def _merge_democratic(self, results: list) -> dict:
        if isinstance(results[0], dict):
            merged = {}
            for r in results:
                if isinstance(r, dict):
                    for k, v in r.items():
                        if k not in merged:
                            merged[k] = v
            return {"merged": True, "result": merged, "method": "democratic_merge"}
        return {"merged": True, "result": results[0], "method": "democratic_first"}

    def _merge_weighted(self, results: list) -> dict:
        return {"merged": True, "result": results[0], "method": "weighted"}

    # ── Swarm Query ───────────────────────────────────────────────────

    def swarm_query(self, query: str, required_capabilities: list = None) -> dict:
        task_id = self.submit_task(
            f"swarm_query_{hashlib.md5(query.encode()).hexdigest()[:8]}",
            query, required_capabilities or ["general"],
        )
        assignments = []
        results = []
        for _ in range(min(3, len(self.agents))):
            assignment = self.assign_next_task()
            if assignment:
                assignments.append(assignment)
                results.append({
                    "agent": assignment["agent"]["name"],
                    "response": f"Agent {assignment['agent']['name']} processing: {query[:80]}",
                })

        merged = self.merge_results(task_id, [r["response"] for r in results])
        return {
            "query": query,
            "agents_involved": len(results),
            "strategy": self.strategy,
            "leader": self.get_leader(),
            "individual_results": results,
            "merged": merged,
            "task_id": task_id,
        }

    # ── Stats ─────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        total = len(self.agents)
        healthy = len(self.get_healthy_agents())
        busy = sum(1 for a in self.agents.values() if a.status == "busy")
        total_tasks = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == "completed")
        failed = sum(1 for t in self.tasks.values() if t.status == "failed")
        return {
            "strategy": self.strategy,
            "total_agents": total,
            "healthy_agents": healthy,
            "busy_agents": busy,
            "leader": self.get_leader(),
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "queued_tasks": len(self.task_queue),
        }

    def save(self) -> dict:
        return {
            "strategy": self.strategy,
            "agents": {aid: a.to_dict() for aid, a in self.agents.items()},
            "tasks": {tid: t.to_dict() for tid, t in self.tasks.items()},
            "task_queue": self.task_queue[:],
            "leader_id": self.leader_id,
            "consensus_threshold": self.consensus_threshold,
        }

    def load(self, data: dict):
        self.strategy = data.get("strategy", "consensus")
        self.agents = {}
        for aid, ad in data.get("agents", {}).items():
            a = SwarmAgent(ad.get("name", aid), ad.get("role", "general"))
            a.__dict__.update(ad)
            self.agents[aid] = a
        self.tasks = {}
        for tid, td in data.get("tasks", {}).items():
            t = SwarmTask(td.get("name", tid), td.get("description", ""))
            t.__dict__.update(td)
            self.tasks[tid] = t
        self.task_queue = data.get("task_queue", [])
        self.leader_id = data.get("leader_id")
        self.consensus_threshold = data.get("consensus_threshold", 0.6)
