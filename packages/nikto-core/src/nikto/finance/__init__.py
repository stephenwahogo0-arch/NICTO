"""Finance Module — BankAccount, BankManager, BankruptcyPrevention."""

import datetime
import random


class BankAccount:
    def __init__(self, account_id: str, name: str, balance: float = 0.0):
        self.account_id = account_id
        self.name = name
        self.balance = balance
        self.transactions = []
        self.created = datetime.datetime.now()

    def deposit(self, amount: float, source: str = "manual") -> dict:
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive"}
        self.balance += amount
        tx = {"type": "deposit", "amount": amount, "source": source,
              "balance_after": self.balance, "timestamp": datetime.datetime.now().isoformat()}
        self.transactions.append(tx)
        return {"success": True, "balance": self.balance, "transaction": tx}

    def withdraw(self, amount: float, destination: str = "manual") -> dict:
        if amount <= 0:
            return {"success": False, "error": "Amount must be positive"}
        if amount > self.balance:
            return {"success": False, "error": "Insufficient funds"}
        self.balance -= amount
        tx = {"type": "withdrawal", "amount": amount, "destination": destination,
              "balance_after": self.balance, "timestamp": datetime.datetime.now().isoformat()}
        self.transactions.append(tx)
        return {"success": True, "balance": self.balance, "transaction": tx}

    def statement(self) -> dict:
        return {
            "account_id": self.account_id,
            "name": self.name,
            "balance": self.balance,
            "transaction_count": len(self.transactions),
            "created": self.created.isoformat()
        }


class BankManager:
    def __init__(self):
        self.accounts = {}

    def create_account(self, name: str, initial_deposit: float = 0.0) -> BankAccount:
        account_id = f"NIKTO-{random.randint(10000, 99999)}"
        acct = BankAccount(account_id, name, initial_deposit)
        self.accounts[account_id] = acct
        return acct

    def get_account(self, account_id: str) -> BankAccount:
        if account_id not in self.accounts:
            raise ValueError(f"Account {account_id} not found")
        return self.accounts[account_id]

    def transfer(self, from_id: str, to_id: str, amount: float) -> dict:
        if from_id not in self.accounts:
            return {"success": False, "error": f"Sender {from_id} not found"}
        if to_id not in self.accounts:
            return {"success": False, "error": f"Receiver {to_id} not found"}
        w = self.accounts[from_id].withdraw(amount, f"transfer to {to_id}")
        if not w["success"]:
            return w
        self.accounts[to_id].deposit(amount, f"transfer from {from_id}")
        return {"success": True, "from_balance": w["balance"],
                "to_balance": self.accounts[to_id].balance, "amount": amount}

    def list_accounts(self) -> list:
        return [a.statement() for a in self.accounts.values()]


class BankruptcyPrevention:
    def __init__(self, bank_manager: BankManager):
        self.bank = bank_manager
        self.minimum_balance = 10.0

    def check_accounts(self) -> list:
        at_risk = []
        for acct in self.bank.accounts.values():
            if acct.balance < self.minimum_balance:
                at_risk.append({
                    "account_id": acct.account_id,
                    "name": acct.name,
                    "balance": acct.balance,
                    "warning": "Balance below minimum threshold"
                })
        return at_risk

    def auto_earn(self, account_id: str, jobs_completed: int = 1, avg_job_value: float = 12.5) -> dict:
        """Record earnings based on completed jobs instead of random simulation."""
        if account_id not in self.bank.accounts:
            return {"success": False, "error": "Account not found"}
        jobs = max(0, int(jobs_completed))
        value = max(0.0, float(avg_job_value))
        if jobs == 0 or value == 0:
            return {"success": False, "error": "No completed jobs to settle"}
        reliability_bonus = min(0.2, jobs / 100)
        earning = round(jobs * value * (1.0 + reliability_bonus), 2)
        return self.bank.accounts[account_id].deposit(earning, "auto_earn_settlement")
