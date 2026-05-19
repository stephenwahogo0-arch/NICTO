"""Finance Manager — tracks earnings and sends payment notifications."""

import json
import logging
import os
import smtplib
import ssl
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from nikto.autopilot.tasks import TaskResult

logger = logging.getLogger(__name__)


class PaymentMethod(str, Enum):
    M_PESA = "mpesa"
    AIRTEL_MONEY = "airtel_money"
    TELKOM = "telkom"
    VISA = "visa"
    MASTERCARD = "mastercard"
    BITCOIN = "bitcoin"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    CUSTOM = "custom"


@dataclass
class TransactionRecord:
    amount_usd: float
    source: str
    method: PaymentMethod
    timestamp: datetime = field(default_factory=datetime.now)
    description: str = ""
    status: str = "completed"
    reference: str = ""

    def to_dict(self) -> dict:
        return {
            "amount_usd": self.amount_usd,
            "source": self.source,
            "method": self.method.value,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "status": self.status,
            "reference": self.reference,
        }


class FinanceManager:
    """Tracks earnings and manages payment notifications."""

    def __init__(self, data_dir: str = "~/.nikto/autopilot"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path = self.data_dir / "ledger.json"
        self.config_path = self.data_dir / "finance_config.json"
        self.transactions: list[TransactionRecord] = []
        self._load_ledger()
        self._payment_config: dict = self._load_config()

    def _load_ledger(self):
        if self.ledger_path.exists():
            try:
                data = json.loads(self.ledger_path.read_text())
                for t in data:
                    t["method"] = PaymentMethod(t["method"])
                    t["timestamp"] = datetime.fromisoformat(t["timestamp"])
                    self.transactions.append(TransactionRecord(**t))
            except Exception as e:
                logger.warning(f"Could not load ledger: {e}")

    def _load_config(self) -> dict:
        if self.config_path.exists():
            try:
                return json.loads(self.config_path.read_text())
            except Exception:
                pass
        return {
            "notifications": {
                "email": {"enabled": False, "address": "", "smtp_host": "", "smtp_port": 587},
                "sms": {"enabled": False, "provider": "", "api_key": ""},
                "file": {"enabled": True, "path": str(self.data_dir / "notifications.log")},
            },
            "payment_methods": {
                "mpesa": {"enabled": False, "phone": "", "provider": "safaricom"},
                "airtel_money": {"enabled": False, "phone": ""},
                "telkom": {"enabled": False, "phone": ""},
                "visa": {"enabled": False, "card_number": "", "expiry": "", "cvv": ""},
                "mastercard": {"enabled": False, "card_number": "", "expiry": "", "cvv": ""},
                "bitcoin": {"enabled": False, "wallet": ""},
            },
        }

    async def save(self):
        data = [t.to_dict() for t in self.transactions]
        self.ledger_path.write_text(json.dumps(data, indent=2))
        self.config_path.write_text(json.dumps(self._payment_config, indent=2))

    async def record_earnings(self, result: TaskResult):
        record = TransactionRecord(
            amount_usd=result.earnings,
            source=result.task_name,
            method=PaymentMethod.BITCOIN,
            description=result.description or f"Earnings from {result.task_name}",
            status="completed" if result.success else "failed",
            reference=result.reference or "",
        )
        self.transactions.append(record)
        await self.save()

    def total_earnings(self) -> float:
        return sum(t.amount_usd for t in self.transactions if t.status == "completed")

    def recent_transactions(self, count: int = 10) -> list[dict]:
        return [t.to_dict() for t in self.transactions[-count:]]

    def get_wallet_summaries(self) -> list[dict]:
        summaries = []
        crypto_conns = [t for t in self.transactions if t.method == PaymentMethod.BITCOIN]
        if crypto_conns:
            total_btc_value = sum(t.amount_usd for t in crypto_conns)
            summaries.append({
                "type": "bitcoin",
                "total_earned_usd": total_btc_value,
                "transactions": len(crypto_conns),
            })
        return summaries

    def get_notification_channels(self) -> list[str]:
        channels = ["file"]
        cfg = self._payment_config.get("notifications", {})
        if cfg.get("email", {}).get("enabled"):
            channels.append("email")
        if cfg.get("sms", {}).get("enabled"):
            channels.append("sms")
        for method_key, method_cfg in self._payment_config.get("payment_methods", {}).items():
            if method_cfg.get("enabled"):
                channels.append(method_key)
        return channels

    async def send_earnings_notification(self, result: TaskResult, channels: list[str]):
        message = self._build_notification(result)
        for channel in channels:
            await self._dispatch_notification(channel, message)
        logger.info(f"Notification sent via {channels}: ${result.earnings:.2f} from {result.task_name}")

    def _build_notification(self, result: TaskResult) -> str:
        lines = [
            f"{'='*50}",
            f"  NIKTO AUTOPILOT — EARNINGS NOTIFICATION",
            f"{'='*50}",
            f"  Task:       {result.task_name}",
            f"  Amount:     ${result.earnings:.2f} USD",
            f"  Status:     {'SUCCESS' if result.success else 'FAILED'}",
            f"  Time:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Reference:  {result.reference or 'N/A'}",
            f"  Description: {result.description or 'Autonomous profit generation'}",
            f"{'='*50}",
            f"  CHECK YOUR CONNECTED WALLETS & M-PESA",
            f"  Available:  M-Pesa | Airtel Money | Telkom",
            f"             Visa | Mastercard | Bitcoin",
            f"{'='*50}",
        ]
        return "\n".join(lines)

    async def _dispatch_notification(self, channel: str, message: str):
        if channel == "file":
            notif_path = Path(self._payment_config.get("notifications", {}).get("file", {}).get("path", str(self.data_dir / "notifications.log")))
            with open(notif_path, "a") as f:
                f.write(f"\n{message}\n")
        elif channel == "email":
            email_cfg = self._payment_config.get("notifications", {}).get("email", {})
            if email_cfg.get("address"):
                try:
                    context = ssl.create_default_context()
                    with smtplib.SMTP(email_cfg["smtp_host"], email_cfg.get("smtp_port", 587)) as server:
                        server.starttls(context=context)
                        server.sendmail("nikto@autopilot", email_cfg["address"], message)
                except Exception as e:
                    logger.warning(f"Email notification failed: {e}")
        else:
            notif_path = self.data_dir / "notifications.log"
            with open(notif_path, "a") as f:
                f.write(f"\n[{channel.upper()}] {message}\n")

    async def refresh_balances(self):
        """Placeholder for periodic balance refresh."""
        pass

    def configure_payment_method(self, method: PaymentMethod, config: dict):
        key = method.value
        if key in self._payment_config.get("payment_methods", {}):
            self._payment_config["payment_methods"][key].update(config)
            self._payment_config["payment_methods"][key]["enabled"] = True
        else:
            self._payment_config.setdefault("payment_methods", {})[key] = {"enabled": True, **config}
        self.config_path.write_text(json.dumps(self._payment_config, indent=2))

    def configure_notification(self, channel: str, config: dict):
        self._payment_config.setdefault("notifications", {})[channel] = config
        self.config_path.write_text(json.dumps(self._payment_config, indent=2))

    def summary(self) -> dict:
        return {
            "total_earnings_usd": self.total_earnings(),
            "transaction_count": len(self.transactions),
            "payment_methods": list(self._payment_config.get("payment_methods", {}).keys()),
            "recent": self.recent_transactions(5),
        }
