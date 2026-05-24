from datetime import datetime


class FinanceManager:
    def __init__(self):
        self._earnings = 0.0
        self._transactions = []

    def total_earnings(self) -> float:
        return self._earnings

    def add_earning(self, amount: float, source: str = "") -> dict:
        self._earnings += amount
        self._transactions.append({"amount": amount, "source": source, "timestamp": datetime.now().isoformat()})
        return {"success": True, "total": self._earnings, "added": amount}
