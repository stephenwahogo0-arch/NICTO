from uuid import uuid4
from datetime import datetime


class EarnWallet:
    def __init__(self, name: str = "default"):
        self.name = name
        self.address = f"0x{str(uuid4())[:40]}"
        self.balance = 0.0

    async def get_balance(self) -> dict:
        return {"success": True, "wallet": self.name, "address": self.address, "balance": self.balance}

    async def credit(self, amount: float, source: str = "") -> dict:
        self.balance += amount
        return {"success": True, "wallet": self.name, "credited": amount, "new_balance": self.balance, "source": source}


async def wallet_stats() -> dict:
    wallet = EarnWallet()
    return {"wallet_name": wallet.name, "wallet_address": wallet.address, "balance": wallet.balance}
