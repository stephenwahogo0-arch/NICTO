from uuid import uuid4


class Task:
    def __init__(self, name: str, description: str, task_type: str, config: dict = None):
        self.id = str(uuid4())[:12]
        self.name = name
        self.description = description
        self.task_type = task_type
        self.config = config or {}


class CryptoMarketMonitor(Task):
    def __init__(self):
        super().__init__("Crypto Market Monitor", "Monitor cryptocurrency market prices", "crypto_market", {"pair": "BTC/USD", "interval": 3600})


class WalletBalanceCheck(Task):
    def __init__(self):
        super().__init__("Wallet Balance Check", "Check cryptocurrency wallet balances", "wallet_balance", {"interval": 86400})


DEFAULT_AUTOPILOT_TASKS = [
    {"name": "Crypto Market Monitor", "description": "Monitor crypto market trends", "type": "crypto_market", "enabled": True},
    {"name": "Wallet Balance Check", "description": "Check wallet balances", "type": "wallet_balance", "enabled": True},
    {"name": "Security Scan", "description": "Run periodic security scans", "type": "security", "enabled": False},
    {"name": "System Health", "description": "Monitor system health metrics", "type": "system_health", "enabled": True},
    {"name": "Network Probe", "description": "Probe network for new devices", "type": "network", "enabled": False},
]
