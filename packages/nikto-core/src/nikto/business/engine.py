"""Real business engine — P&L tracking with persistent state."""
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Optional


class BusinessType(Enum):
    CONTENT = "content"
    SERVICE = "service"
    DIGITAL = "digital"
    MICRO = "micro"

class BusinessStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class BusinessUnit:
    def __init__(self, name: str, btype: "BusinessType", budget: float = 0.0):
        self.name = name
        self.type = btype
        self.budget = budget


BUSINESS_TEMPLATES = {
    "ecommerce": {"name": "E-Commerce", "type": BusinessType.DIGITAL, "setup_cost": 100},
    "consulting": {"name": "Consulting", "type": BusinessType.SERVICE, "setup_cost": 50},
    "content": {"name": "Content Creation", "type": BusinessType.CONTENT, "setup_cost": 25},
    "micro_saas": {"name": "Micro SaaS", "type": BusinessType.DIGITAL, "setup_cost": 200},
}


class BusinessEngine:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or os.path.join(str(Path.home()), ".nikto", "business"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.data_dir / "businesses.json"
        self.businesses = self._load()

    def _load(self) -> dict:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception:
                pass
        return {}

    def _save(self):
        self.state_file.write_text(json.dumps(self.businesses, indent=2))

    def create_business(self, name: str, btype: BusinessType = BusinessType.DIGITAL) -> dict:
        bid = uuid.uuid4().hex[:12]
        self.businesses[bid] = {"id": bid, "name": name, "type": btype.value, "status": "active",
                                "revenue": 0.0, "costs": 0.0, "profit": 0.0, "transactions": [],
                                "created": time.time()}
        self._save()
        return self.businesses[bid]

    def add_revenue(self, business_id: str, amount: float, source: str = ""):
        biz = self.businesses.get(business_id)
        if not biz:
            return False
        biz["revenue"] += amount
        biz["profit"] = biz["revenue"] - biz["costs"]
        biz["transactions"].append({"type": "revenue", "amount": amount, "source": source, "time": time.time()})
        self._save()
        return True

    def add_cost(self, business_id: str, amount: float, category: str = ""):
        biz = self.businesses.get(business_id)
        if not biz:
            return False
        biz["costs"] += amount
        biz["profit"] = biz["revenue"] - biz["costs"]
        biz["transactions"].append({"type": "cost", "amount": amount, "category": category, "time": time.time()})
        self._save()
        return True

    def get_business(self, business_id: str) -> Optional[dict]:
        return self.businesses.get(business_id)

    def list_businesses(self) -> list:
        return [{"id": bid, "name": b["name"], "type": b["type"], "status": b["status"],
                 "revenue": b["revenue"], "costs": b["costs"], "profit": b["profit"]}
                for bid, b in self.businesses.items()]

    def get_total_profit(self) -> float:
        return sum(b.get("profit", 0) for b in self.businesses.values())
