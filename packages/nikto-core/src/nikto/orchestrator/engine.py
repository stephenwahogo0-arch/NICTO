from enum import Enum
from uuid import uuid4
from datetime import datetime


class Priority(Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Budget:
    def __init__(self, max_operations: int = 100):
        self.max_operations = max_operations
        self.used = 0

    def can_proceed(self) -> bool:
        return self.used < self.max_operations

    def consume(self, amount: int = 1):
        self.used += amount

    def remaining(self) -> int:
        return self.max_operations - self.used


class OrchestratorConfig:
    def __init__(self, max_agents: int = 10, max_concurrent_tasks: int = 5):
        self.max_agents = max_agents
        self.max_concurrent_tasks = max_concurrent_tasks


class Orchestrator:
    def __init__(self, config: OrchestratorConfig = None):
        self.config = config or OrchestratorConfig()
        self.agents = {}
        self.tickets = {}
        self.budget = Budget()

    def add_agent(self, name: str, agent_type: str, config: dict = None) -> dict:
        agent_id = str(uuid4())[:12]
        self.agents[agent_id] = {"id": agent_id, "name": name, "type": agent_type, "config": config or {}, "created_at": datetime.now().isoformat()}
        return self.agents[agent_id]

    def create_ticket(self, title: str, description: str, priority: Priority = Priority.MEDIUM) -> dict:
        ticket_id = str(uuid4())[:12]
        self.tickets[ticket_id] = {"id": ticket_id, "title": title, "description": description, "priority": priority, "status": TicketStatus.OPEN, "assigned_to": None, "created_at": datetime.now().isoformat()}
        return self.tickets[ticket_id]

    def assign_ticket(self, ticket_id: str, agent_id: str) -> dict:
        if ticket_id not in self.tickets:
            return {"success": False, "error": "Ticket not found"}
        if agent_id not in self.agents:
            return {"success": False, "error": "Agent not found"}
        self.tickets[ticket_id]["assigned_to"] = agent_id
        self.tickets[ticket_id]["status"] = TicketStatus.IN_PROGRESS
        return {"success": True, "ticket_id": ticket_id, "agent_id": agent_id}

    def report_ticket(self, ticket_id: str, status: TicketStatus, result: str = "") -> dict:
        if ticket_id not in self.tickets:
            return {"success": False, "error": "Ticket not found"}
        self.tickets[ticket_id]["status"] = status
        self.tickets[ticket_id]["result"] = result
        self.tickets[ticket_id]["resolved_at"] = datetime.now().isoformat()
        return {"success": True, "ticket_id": ticket_id, "status": status.value}

    def status(self) -> dict:
        return {
            "agents": len(self.agents),
            "tickets": len(self.tickets),
            "open_tickets": sum(1 for t in self.tickets.values() if t["status"] == TicketStatus.OPEN),
            "budget_remaining": self.budget.remaining(),
            "max_agents": self.config.max_agents,
        }
