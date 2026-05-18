import asyncio
import enum
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TicketStatus(enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"


class Priority(enum.Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


@dataclass
class Ticket:
    id: str = field(default_factory=lambda: f"TICK-{uuid.uuid4().hex[:8].upper()}")
    title: str = ""
    description: str = ""
    status: TicketStatus = TicketStatus.PENDING
    priority: Priority = Priority.MEDIUM
    assignee: str = ""
    parent_id: Optional[str] = None
    subtasks: list = field(default_factory=list)
    budget: float = 0.0
    cost: float = 0.0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "title": self.title, "description": self.description,
            "status": self.status.value, "priority": self.priority.name,
            "assignee": self.assignee, "parent_id": self.parent_id,
            "subtasks": self.subtasks, "budget": self.budget, "cost": self.cost,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }


@dataclass
class AgentNode:
    name: str
    role: str = "worker"
    skills: list = field(default_factory=list)
    status: str = "idle"
    current_ticket: Optional[str] = None
    completed: int = 0
    failed: int = 0
    total_cost: float = 0.0
    last_heartbeat: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name, "role": self.role,
            "skills": self.skills, "status": self.status,
            "current_ticket": self.current_ticket,
            "completed": self.completed, "failed": self.failed,
            "total_cost": self.total_cost,
        }


@dataclass
class Heartbeat:
    agent_name: str
    timestamp: float = field(default_factory=time.time)
    status: str = "alive"
    cpu: float = 0.0
    memory: float = 0.0
    message: str = ""


@dataclass
class Budget:
    total: float = 1000.0
    spent: float = 0.0
    currency: str = "USD"
    reset_period: str = "monthly"

    def remaining(self) -> float:
        return self.total - self.spent

    def can_spend(self, amount: float) -> bool:
        return self.spent + amount <= self.total


@dataclass
class OrchestratorConfig:
    name: str = "nikto-orchestrator"
    max_concurrent: int = 5
    heartbeat_interval: float = 30.0
    ticket_timeout: float = 3600.0
    budget: Budget = field(default_factory=Budget)
    org_chart_file: str = str(Path.home() / ".nikto" / "org_chart.json")


class Orchestrator:
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        self.agents: dict[str, AgentNode] = {}
        self.tickets: dict[str, Ticket] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def add_agent(self, name: str, role: str = "worker", skills: list = None) -> AgentNode:
        agent = AgentNode(name=name, role=role, skills=skills or [])
        self.agents[name] = agent
        self._save_org_chart()
        return agent

    def remove_agent(self, name: str) -> bool:
        if name in self.agents:
            del self.agents[name]
            self._save_org_chart()
            return True
        return False

    def create_ticket(self, title: str, description: str = "", priority: Priority = Priority.MEDIUM,
                      parent_id: str = "", budget: float = 0.0) -> Ticket:
        ticket = Ticket(
            title=title, description=description, priority=priority,
            parent_id=parent_id or None, budget=budget,
        )
        self.tickets[ticket.id] = ticket
        return ticket

    def assign_ticket(self, ticket_id: str, agent_name: str) -> bool:
        ticket = self.tickets.get(ticket_id)
        agent = self.agents.get(agent_name)
        if not ticket or not agent:
            return False
        ticket.status = TicketStatus.ASSIGNED
        ticket.assignee = agent_name
        ticket.updated_at = time.time()
        agent.current_ticket = ticket_id
        agent.status = "busy"
        return True

    async def run(self):
        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"Orchestrator '{self.config.name}' started")
        return {"status": "started", "agents": len(self.agents)}

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _heartbeat_loop(self):
        while self._running:
            for agent in self.agents.values():
                if agent.last_heartbeat and time.time() - agent.last_heartbeat > self.config.heartbeat_interval * 3:
                    agent.status = "unreachable"
                    logger.warning(f"Agent '{agent.name}' missed heartbeat")
            await asyncio.sleep(self.config.heartbeat_interval)

    def report_ticket(self, ticket_id: str, status: TicketStatus, cost: float = 0.0) -> bool:
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return False
        ticket.status = status
        ticket.cost = cost
        ticket.updated_at = time.time()
        self.config.budget.spent += cost
        if ticket.assignee and status == TicketStatus.DONE:
            agent = self.agents.get(ticket.assignee)
            if agent:
                agent.completed += 1
                agent.status = "idle"
                agent.current_ticket = None
                agent.total_cost += cost
        return True

    def status(self) -> dict:
        return {
            "name": self.config.name,
            "running": self._running,
            "agents": len(self.agents),
            "tickets": len(self.tickets),
            "active_tickets": sum(1 for t in self.tickets.values() if t.status in (TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS)),
            "budget_remaining": self.config.budget.remaining(),
            "budget_spent": self.config.budget.spent,
        }

    def _save_org_chart(self):
        data = [a.to_dict() for a in self.agents.values()]
        Path(self.config.org_chart_file).write_text(json.dumps(data, indent=2))
