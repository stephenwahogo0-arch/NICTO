import enum
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


class BusinessType(enum.Enum):
    CONTENT = "content"
    SERVICE = "service"
    DIGITAL = "digital"
    AFFILIATE = "affiliate"
    MICRO = "micro"


class BusinessStatus(enum.Enum):
    LAUNCHED = "launched"
    OPERATING = "operating"
    SCALING = "scaling"
    PAUSED = "paused"
    CLOSED = "closed"


@dataclass
class BusinessUnit:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    btype: BusinessType = BusinessType.SERVICE
    status: BusinessStatus = BusinessStatus.LAUNCHED
    description: str = ""
    agent_ids: list[str] = field(default_factory=list)
    tasks: list[dict] = field(default_factory=list)
    revenue: float = 0.0
    costs: float = 0.0
    profit: float = 0.0
    milestones: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "btype": self.btype.value,
            "status": self.status.value,
            "description": self.description,
            "agent_ids": self.agent_ids,
            "tasks": self.tasks,
            "revenue": self.revenue,
            "costs": self.costs,
            "profit": self.profit,
            "milestones": self.milestones,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BusinessUnit":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", ""),
            btype=BusinessType(data.get("btype", "service")),
            status=BusinessStatus(data.get("status", "launched")),
            description=data.get("description", ""),
            agent_ids=data.get("agent_ids", []),
            tasks=data.get("tasks", []),
            revenue=data.get("revenue", 0.0),
            costs=data.get("costs", 0.0),
            profit=data.get("profit", 0.0),
            milestones=data.get("milestones", []),
            created_at=data.get("created_at", time.time()),
            metadata=data.get("metadata", {}),
        )


BUSINESS_TEMPLATES = {
    "content": {
        "name": "Content Studio",
        "description": "Zero-capital content creation business. Produces articles, videos, graphics using NIKTO's tools.",
        "initial_tasks": [
            "Research trending topics in AI and technology",
            "Generate 5 article outlines with SEO keywords",
            "Create 2 digital graphics for social media",
            "Schedule content calendar for 30 days",
        ],
    },
    "service": {
        "name": "Digital Services Agency",
        "description": "Zero-capital service business. Offers development, consulting, design, and automation services.",
        "initial_tasks": [
            "Create service catalog with pricing tiers",
            "Build portfolio from generated samples",
            "Generate outreach templates for 50 prospects",
            "Set up automated proposal generator",
        ],
    },
    "digital": {
        "name": "Digital Products Store",
        "description": "Zero-capital digital products business. Creates templates, code, assets, and digital downloads.",
        "initial_tasks": [
            "Brainstorm 10 digital product ideas with market demand",
            "Generate 3 product prototypes (templates/scripts/assets)",
            "Create product descriptions and marketing copy",
            "Set up distribution channels",
        ],
    },
    "affiliate": {
        "name": "Affiliate Marketing Hub",
        "description": "Zero-capital affiliate business. Promotes products through content, reviews, and comparisons.",
        "initial_tasks": [
            "Research high-commission affiliate programs",
            "Generate 5 product review articles with affiliate links",
            "Create comparison charts for top products",
            "Build email capture lead magnet",
        ],
    },
    "micro": {
        "name": "Micro Business Collective",
        "description": "Zero-capital micro-business network. Completes small paid tasks, micro-services, and gigs.",
        "initial_tasks": [
            "List 20 micro-services NIKTO can offer (writing, coding, analysis)",
            "Generate 10 sample deliverables",
            "Create gig listings for freelance platforms",
            "Set up automated delivery pipeline",
        ],
    },
}


class BusinessEngine:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.nikto").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.data_dir / "businesses.json"
        self.businesses: dict[str, BusinessUnit] = {}
        self._load()

    def _load(self):
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text())
                self.businesses = {
                    bid: BusinessUnit.from_dict(b) for bid, b in data.items()
                }
            except Exception:
                self.businesses = {}

    def _save(self):
        data = {bid: b.to_dict() for bid, b in self.businesses.items()}
        self.store_path.write_text(json.dumps(data, indent=2))

    def start_business(self, btype: str, name: str = "", description: str = "") -> dict:
        try:
            btype_enum = BusinessType(btype)
        except ValueError:
            return {"success": False, "error": f"Invalid business type: {btype}. Valid: content, service, digital, affiliate, micro"}

        template = BUSINESS_TEMPLATES.get(btype, {})
        unit = BusinessUnit(
            name=name or template.get("name", f"{btype.title()} Business"),
            btype=btype_enum,
            description=description or template.get("description", ""),
            tasks=[{"id": str(uuid.uuid4())[:8], "title": t, "status": "pending", "assigned_to": ""} for t in template.get("initial_tasks", [])],
        )
        self.businesses[unit.id] = unit
        self._save()
        return {"success": True, "business": unit.to_dict()}

    def assign_agent(self, business_id: str, agent_id: str) -> dict:
        if business_id not in self.businesses:
            return {"success": False, "error": "Business not found"}
        biz = self.businesses[business_id]
        if agent_id not in biz.agent_ids:
            biz.agent_ids.append(agent_id)
        self._save()
        return {"success": True, "business_id": business_id, "agents": biz.agent_ids}

    def add_task(self, business_id: str, title: str) -> dict:
        if business_id not in self.businesses:
            return {"success": False, "error": "Business not found"}
        task = {"id": str(uuid.uuid4())[:8], "title": title, "status": "pending", "assigned_to": ""}
        self.businesses[business_id].tasks.append(task)
        self._save()
        return {"success": True, "task": task}

    def complete_task(self, business_id: str, task_id: str) -> dict:
        if business_id not in self.businesses:
            return {"success": False, "error": "Business not found"}
        biz = self.businesses[business_id]
        for t in biz.tasks:
            if t["id"] == task_id:
                t["status"] = "completed"
                t["completed_at"] = time.time()
                break
        self._save()
        return {"success": True, "business_id": business_id, "task_id": task_id}

    def add_revenue(self, business_id: str, amount: float, source: str = "") -> dict:
        if business_id not in self.businesses:
            return {"success": False, "error": "Business not found"}
        biz = self.businesses[business_id]
        biz.revenue += amount
        biz.profit = biz.revenue - biz.costs
        entry = {"amount": amount, "source": source, "timestamp": time.time()}
        biz.metadata.setdefault("revenue_entries", []).append(entry)
        self._save()
        return {"success": True, "revenue": biz.revenue, "profit": biz.profit}

    def add_cost(self, business_id: str, amount: float, description: str = "") -> dict:
        if business_id not in self.businesses:
            return {"success": False, "error": "Business not found"}
        biz = self.businesses[business_id]
        biz.costs += amount
        biz.profit = biz.revenue - biz.costs
        entry = {"amount": amount, "description": description, "timestamp": time.time()}
        biz.metadata.setdefault("cost_entries", []).append(entry)
        self._save()
        return {"success": True, "costs": biz.costs, "profit": biz.profit}

    def scale_business(self, business_id: str) -> dict:
        if business_id not in self.businesses:
            return {"success": False, "error": "Business not found"}
        biz = self.businesses[business_id]
        biz.status = BusinessStatus.SCALING
        scale_tasks = [
            f"Scale {biz.name} - hire/assign 2 more sub-agents",
            f"Expand {biz.name} offering to 3 new verticals",
            f"Automate {biz.name} delivery pipeline",
            f"Set up recurring revenue model for {biz.name}",
        ]
        for t in scale_tasks:
            biz.tasks.append({"id": str(uuid.uuid4())[:8], "title": t, "status": "pending", "assigned_to": ""})
        self._save()
        return {"success": True, "business": biz.to_dict(), "new_tasks": scale_tasks}

    def get_status(self, business_id: Optional[str] = None) -> dict:
        if business_id:
            if business_id not in self.businesses:
                return {"success": False, "error": "Business not found"}
            return {"success": True, "business": self.businesses[business_id].to_dict()}
        return {
            "success": True,
            "total_businesses": len(self.businesses),
            "businesses": {bid: b.to_dict() for bid, b in self.businesses.items()},
        }

    def list_businesses(self) -> list[dict]:
        return [b.to_dict() for b in self.businesses.values()]

    def pause_business(self, business_id: str) -> dict:
        if business_id not in self.businesses:
            return {"success": False, "error": "Business not found"}
        self.businesses[business_id].status = BusinessStatus.PAUSED
        self._save()
        return {"success": True, "business_id": business_id, "status": "paused"}

    def total_revenue(self) -> float:
        return sum(b.revenue for b in self.businesses.values())

    def total_profit(self) -> float:
        return sum(b.profit for b in self.businesses.values())

    def summary(self) -> dict:
        types = {}
        statuses = {}
        for b in self.businesses.values():
            t = b.btype.value
            types[t] = types.get(t, 0) + 1
            s = b.status.value
            statuses[s] = statuses.get(s, 0) + 1
        return {
            "total": len(self.businesses),
            "by_type": types,
            "by_status": statuses,
            "total_revenue": self.total_revenue(),
            "total_profit": self.total_profit(),
            "total_agents": sum(len(b.agent_ids) for b in self.businesses.values()),
            "total_tasks": sum(len(b.tasks) for b in self.businesses.values()),
        }
