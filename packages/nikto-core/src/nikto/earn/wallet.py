"""Real wallet engine — persistent wallet with address generation."""
import json
import os
import time
import uuid
from pathlib import Path
from typing import Optional


class EarnWallet:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or os.path.join(str(Path.home()), ".nikto", "wallet"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.wallet_file = self.data_dir / "wallet.json"
        self.wallet = self._load()

    def _load(self) -> dict:
        if self.wallet_file.exists():
            try:
                return json.loads(self.wallet_file.read_text())
            except Exception:
                pass
        return {"address": f"nk{os.urandom(20).hex()[:38]}", "balance": 0.0, "transactions": [], "created": time.time()}

    def _save(self):
        self.wallet_file.write_text(json.dumps(self.wallet, indent=2))

    def credit(self, amount: float, source: str = "mining"):
        self.wallet["balance"] += amount
        self.wallet["transactions"].append({"type": "credit", "amount": amount, "source": source, "time": time.time()})
        self._save()
        return self.wallet["balance"]

    def debit(self, amount: float, destination: str = ""):
        if self.wallet["balance"] < amount:
            return False
        self.wallet["balance"] -= amount
        self.wallet["transactions"].append({"type": "debit", "amount": amount, "destination": destination, "time": time.time()})
        self._save()
        return True

    def get_balance(self) -> float:
        return self.wallet["balance"]

    def get_address(self) -> str:
        return self.wallet["address"]

    def get_history(self, limit: int = 50) -> list:
        return self.wallet["transactions"][-limit:]

    def get_summary(self) -> dict:
        return {"address": self.wallet["address"], "balance": self.wallet["balance"],
                "transactions": len(self.wallet["transactions"]), "created": self.wallet["created"]}


def wallet_stats(wallet: EarnWallet) -> dict:
    s = wallet.get_summary()
    s["total_earned"] = sum(t["amount"] for t in wallet.get_history() if t["type"] == "credit")
    s["total_spent"] = sum(t["amount"] for t in wallet.get_history() if t["type"] == "debit")
    return s
