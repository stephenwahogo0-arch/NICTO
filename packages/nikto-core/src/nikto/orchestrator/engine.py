"""NIKTO Orchestrator Engine — coordinates brain subsystems into coherent workflows."""

import json
import hashlib
import uuid
import time
from datetime import datetime, timezone
from typing import Optional


class WorkflowStep:
    def __init__(self, name: str, target: str, params: dict = None,
                 depends_on: list = None, priority: int = 5,
                 timeout: float = 30.0):
        self.id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]
        self.name = name
        self.target = target
        self.params = params or {}
        self.depends_on = depends_on or []
        self.priority = max(1, min(10, priority))
        self.timeout = timeout
        self.status = "pending"
        self.result = None
        self.error = None
        self.started_at = None
        self.completed_at = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class Workflow:
    def __init__(self, name: str, description: str = "",
                 metadata: dict = None):
        self.id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]
        self.name = name
        self.description = description
        self.steps = []
        self.status = "idle"
        self.created = datetime.now(timezone.utc).isoformat()
        self.completed_at = None
        self.metadata = metadata or {}

    def add_step(self, name: str, target: str, params: dict = None,
                 depends_on: list = None, priority: int = 5) -> str:
        step = WorkflowStep(name, target, params, depends_on, priority)
        self.steps.append(step)
        return step.id

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoOrchestrator:
    """
    Orchestrator Engine.
    Coordinates brain subsystems into workflows.
    Manages workflow lifecycle, step execution, and error recovery.
    """

    SUBSYSTEMS = {
        "reasoner": "Analytical and multi-style reasoning",
        "knowledge": "Fact and concept storage and retrieval",
        "memory": "Long-term memory with consolidation and recall",
        "emotion": "Emotional state tracking and regulation",
        "conscience": "Ethical and moral evaluation",
        "truth_engine": "Fact-checking and anti-hallucination",
        "dream_steerer": "Latent-space thought augmentation",
        "swarm": "Multi-agent coordination and task distribution",
        "performance_graph": "Metric tracking and trend analysis",
        "learner": "Skill acquisition and mastery tracking",
        "goals": "Hierarchical goal management",
        "language": "Natural language understanding and generation",
    }

    def __init__(self):
        self.workflows = {}
        self.max_workflows = 100
        self.routing_tables = {}  # intent -> subsystem

    # ── Workflow Management ───────────────────────────────────────────

    def create_workflow(self, name: str, description: str = "",
                        metadata: dict = None) -> str:
        wf = Workflow(name, description, metadata)
        self.workflows[wf.id] = wf
        if len(self.workflows) > self.max_workflows:
            oldest = min(self.workflows.keys(),
                        key=lambda k: self.workflows[k].created)
            del self.workflows[oldest]
        return wf.id

    def add_step(self, workflow_id: str, step_name: str, target: str,
                 params: dict = None, depends_on: list = None,
                 priority: int = 5) -> Optional[str]:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return None
        return wf.add_step(step_name, target, params, depends_on, priority)

    def get_workflow(self, workflow_id: str) -> Optional[dict]:
        wf = self.workflows.get(workflow_id)
        return wf.to_dict() if wf else None

    def list_workflows(self, status: str = None) -> list:
        wfs = self.workflows.values()
        if status:
            wfs = [w for w in wfs if w.status == status]
        return [w.to_dict() for w in wfs]

    # ── Execution ─────────────────────────────────────────────────────

    def execute_workflow(self, workflow_id: str,
                         subsystem_providers: dict = None) -> dict:
        wf = self.workflows.get(workflow_id)
        if not wf:
            return {"success": False, "error": "Workflow not found"}
        wf.status = "running"
        wf.started_at = datetime.now(timezone.utc).isoformat()
        completed = {}
        step_results = []

        # Topological sort by dependency
        sorted_steps = self._topological_sort(wf.steps)
        for step in sorted_steps:
            deps_met = all(d in completed for d in step.depends_on)
            if not deps_met:
                step.status = "blocked"
                step.error = "Unmet dependencies"
                continue
            step.status = "in_progress"
            step.started_at = datetime.now(timezone.utc).isoformat()
            try:
                provider = subsystem_providers or {}
                result = self._execute_step(step, provider)
                step.status = "completed"
                step.result = result
                completed[step.id] = result
            except Exception as e:
                step.status = "failed"
                step.error = str(e)
            step.completed_at = datetime.now(timezone.utc).isoformat()
            step_results.append(step.to_dict())

        has_failures = any(s.status == "failed" for s in wf.steps)
        wf.status = "completed_with_errors" if has_failures else "completed"
        wf.completed_at = datetime.now(timezone.utc).isoformat()

        return {
            "workflow_id": workflow_id,
            "workflow_name": wf.name,
            "status": wf.status,
            "total_steps": len(wf.steps),
            "completed_steps": sum(1 for s in wf.steps if s.status == "completed"),
            "failed_steps": sum(1 for s in wf.steps if s.status == "failed"),
            "blocked_steps": sum(1 for s in wf.steps if s.status == "blocked"),
            "steps": step_results,
        }

    def _execute_step(self, step: WorkflowStep,
                      providers: dict) -> any:
        target = step.target
        params = step.params
        if target in providers:
            provider = providers[target]
            action = params.get("action", "process")
            method = getattr(provider, action, None)
            if method:
                args = params.get("args", [])
                kwargs = params.get("kwargs", {})
                return method(*args, **kwargs)
        return {
            "target": target,
            "params": params,
            "note": "Simulated execution (no provider registered)",
        }

    def _topological_sort(self, steps: list) -> list:
        step_ids = {s.id: s for s in steps}
        visited = set()
        result = []
        def dfs(sid):
            if sid in visited:
                return
            visited.add(sid)
            step = step_ids[sid]
            for dep_id in step.depends_on:
                if dep_id in step_ids:
                    dfs(dep_id)
            result.append(step)
        for s in steps:
            dfs(s.id)
        return result

    # ── Routing ───────────────────────────────────────────────────────

    def route_intent(self, intent: str, subsystem: str):
        self.routing_tables[intent] = subsystem

    def resolve_intent(self, intent: str) -> Optional[str]:
        return self.routing_tables.get(intent)

    def suggest_routing(self, input_text: str) -> str:
        text = input_text.lower()
        if any(w in text for w in ["think", "reason", "analyze", "solve"]):
            return "reasoner"
        if any(w in text for w in ["remember", "recall", "memory", "forget"]):
            return "memory"
        if any(w in text for w in ["learn", "teach", "skill", "practice"]):
            return "learner"
        if any(w in text for w in ["emotion", "feel", "mood", "happy", "sad"]):
            return "emotion"
        if any(w in text for w in ["goal", "plan", "objective", "mission"]):
            return "goals"
        if any(w in text for w in ["truth", "fact", "verify", "check", "correct"]):
            return "truth_engine"
        if any(w in text for w in ["dream", "steer", "augment", "creative"]):
            return "dream_steerer"
        if any(w in text for w in ["swarm", "agent", "multi", "distribute"]):
            return "swarm"
        if any(w in text for w in ["knowledge", "fact", "concept", "what is"]):
            return "knowledge"
        return "reasoner"

    # ── Health ────────────────────────────────────────────────────────

    def health_check(self) -> dict:
        return {
            "subsystem_count": len(self.SUBSYSTEMS),
            "active_workflows": len(self.list_workflows("running")),
            "total_workflows": len(self.workflows),
            "routing_entries": len(self.routing_tables),
            "subsystems": {k: v for k, v in self.SUBSYSTEMS.items()},
        }

    def save(self) -> dict:
        return {
            "workflows": {wid: wf.to_dict() for wid, wf in self.workflows.items()},
            "routing_tables": self.routing_tables,
        }

    def load(self, data: dict):
        self.workflows = {}
        for wid, wd in data.get("workflows", {}).items():
            wf = Workflow(wd.get("name", wid), wd.get("description", ""))
            wf.__dict__.update(wd)
            wf.steps = []
            for sd in wd.get("steps", []):
                step = WorkflowStep(sd["name"], sd["target"])
                step.__dict__.update(sd)
                wf.steps.append(step)
            self.workflows[wid] = wf
        self.routing_tables = data.get("routing_tables", {})
