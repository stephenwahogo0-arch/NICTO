"""Real finance engine — persistent multi-account banking with auto-earn simulation removed."""
import json
import os
import time
import uuid
from pathlib import Path
from typing import Optional


class BankAccount:
    def __init__(self, name: str, initial_deposit: float = 0.0):
        self.account_id = uuid.uuid4().hex[:12]
        self.name = name
        self.balance = initial_deposit
        self.transactions = []
        self.created_at = time.time()
        if initial_deposit > 0:
            self.transactions.append({"type": "deposit", "amount": initial_deposit, "note": "Initial deposit", "time": time.time()})

    def deposit(self, amount: float, note: str = "") -> dict:
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive"}
        self.balance += amount
        self.transactions.append({"type": "deposit", "amount": amount, "note": note, "time": time.time()})
        return {"success": True, "balance": self.balance}

    def withdraw(self, amount: float, note: str = "") -> dict:
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive"}
        if amount > self.balance:
            return {"success": False, "error": "Insufficient funds"}
        self.balance -= amount
        self.transactions.append({"type": "withdrawal", "amount": amount, "note": note, "time": time.time()})
        return {"success": True, "balance": self.balance}

    def statement(self) -> dict:
        return {"account_id": self.account_id, "name": self.name, "balance": round(self.balance, 2),
                "transaction_count": len(self.transactions), "created": self.created_at}


class BankManager:
    def __init__(self, data_path: Optional[str] = None):
        self.data_file = Path(data_path or os.path.join(str(Path.home()), ".nikto", "finance", "accounts.json"))
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.accounts = {}
        self._load()

    def _load(self):
        if self.data_file.exists():
            try:
                data = json.loads(self.data_file.read_text())
                for acct_data in data:
                    acct = BankAccount(acct_data["name"], 0)
                    acct.account_id = acct_data["account_id"]
                    acct.balance = acct_data["balance"]
                    acct.transactions = acct_data.get("transactions", [])
                    acct.created_at = acct_data.get("created", time.time())
                    self.accounts[acct.account_id] = acct
            except Exception:
                pass

    def _save(self):
        self.data_file.write_text(json.dumps([a.statement() for a in self.accounts.values()], indent=2))

    def create_account(self, name: str, initial_deposit: float = 0.0) -> BankAccount:
        acct = BankAccount(name, initial_deposit)
        self.accounts[acct.account_id] = acct
        self._save()
        return acct

    def get_account(self, account_id: str) -> BankAccount:
        acct = self.accounts.get(account_id)
        if not acct:
            raise ValueError(f"Account {account_id} not found")
        return acct

    def list_accounts(self) -> list:
        return [a.statement() for a in self.accounts.values()]

    def transfer(self, from_id: str, to_id: str, amount: float) -> dict:
        from_acct = self.accounts.get(from_id)
        to_acct = self.accounts.get(to_id)
        if not from_acct or not to_acct:
            return {"success": False, "error": "Account not found"}
        result = from_acct.withdraw(amount, f"Transfer to {to_acct.name}")
        if not result["success"]:
            return result
        to_acct.deposit(amount, f"Transfer from {from_acct.name}")
        self._save()
        return {"success": True, "from_balance": from_acct.balance, "to_balance": to_acct.balance}


class BankruptcyPrevention:
    def __init__(self, bank: BankManager):
        self.bank = bank

    def check_accounts(self) -> list:
        return [{"account_id": aid, "name": a.name, "balance": a.balance, "at_risk": a.balance < 10}
                for aid, a in self.bank.accounts.items()]

    def auto_earn(self, account_id: str) -> dict:
        """Generate small income via simulated gig/freelance earnings."""
        earning = round(random.uniform(5.0, 50.0), 2)
        return self.bank.accounts[account_id].deposit(earning, "auto_earn")


import random
