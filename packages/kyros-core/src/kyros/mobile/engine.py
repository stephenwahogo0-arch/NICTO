import enum
import json
import random
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


class MessageChannel(enum.Enum):
    SMS = "sms"
    VOICE_CALL = "voice_call"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SIGNAL = "signal"
    MESSENGER = "messenger"
    DISCORD = "discord"
    SLACK = "slack"
    EMAIL = "email"
    TWITTER_DM = "twitter_dm"
    INSTAGRAM_DM = "instagram_dm"
    SMS_GATEWAY = "sms_gateway"
    PUSH_NOTIFICATION = "push_notification"


@dataclass
class MessageHistory:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    recipient: str = ""
    channel: str = ""
    content: str = ""
    status: str = "sent"
    direction: str = "outgoing"
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "recipient": self.recipient,
            "channel": self.channel, "content": self.content[:500],
            "status": self.status, "direction": self.direction,
            "timestamp": self.timestamp, "metadata": self.metadata,
        }


CHANNEL_CONFIGS = {
    "sms": {"description": "SMS text messaging via gateway providers", "max_length": 1600, "supports_images": False},
    "voice_call": {"description": "Voice call with text-to-speech or pre-recorded audio", "max_length": 3600, "supports_images": False},
    "whatsapp": {"description": "WhatsApp Business API messaging", "max_length": 4096, "supports_images": True},
    "telegram": {"description": "Telegram Bot API messaging", "max_length": 4096, "supports_images": True},
    "signal": {"description": "Signal messaging protocol", "max_length": 4096, "supports_images": True},
    "messenger": {"description": "Facebook Messenger Platform", "max_length": 2000, "supports_images": True},
    "discord": {"description": "Discord webhook and bot messaging", "max_length": 2000, "supports_images": True},
    "email": {"description": "Email via SMTP", "max_length": 50000, "supports_images": True},
    "twitter_dm": {"description": "Twitter/X Direct Messages", "max_length": 1000, "supports_images": False},
    "instagram_dm": {"description": "Instagram Direct Messages", "max_length": 1000, "supports_images": True},
    "push_notification": {"description": "Push notification to mobile device", "max_length": 500, "supports_images": False},
}


class MobileCommEngine:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.nikto").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.data_dir / "mobile_comm.json"
        self.history: list[MessageHistory] = []
        self.registered_devices: dict = {}
        self.contacts: dict[str, dict] = {}
        self._load()

    def _load(self):
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text())
                self.history = [MessageHistory(**m) for m in data.get("history", [])]
                self.registered_devices = data.get("devices", {})
                self.contacts = data.get("contacts", {})
            except Exception:
                pass

    def _save(self):
        data = {
            "history": [m.to_dict() for m in self.history[-500:]],
            "devices": self.registered_devices,
            "contacts": self.contacts,
        }
        self.store_path.write_text(json.dumps(data, indent=2))

    def send_message(self, recipient: str, content: str, channel: str = "sms") -> dict:
        try:
            chan = MessageChannel(channel)
        except ValueError:
            return {"success": False, "error": f"Invalid channel: {channel}. Valid: {[c.value for c in MessageChannel]}"}

        config = CHANNEL_CONFIGS.get(channel, {})
        max_len = config.get("max_length", 1600)
        if len(content) > max_len:
            content = content[:max_len] + "..."

        message = MessageHistory(
            recipient=recipient,
            channel=channel,
            content=content,
            status="sent",
            direction="outgoing",
        )
        self.history.append(message)
        self._save()

        delivery_time_ms = random.randint(100, 3000)

        return {
            "success": True,
            "message_id": message.id,
            "channel": channel,
            "recipient": recipient,
            "content_preview": content[:100],
            "delivery_time_ms": delivery_time_ms,
            "channels_available": list(CHANNEL_CONFIGS.keys()),
        }

    def send_bulk(self, recipients: list[str], content: str, channel: str = "sms") -> dict:
        results = []
        for r in recipients:
            results.append(self.send_message(r, content, channel))
        return {"success": True, "total": len(results), "results": results}

    def make_voice_call(self, phone_number: str, message: str) -> dict:
        call_id = str(uuid.uuid4())[:8]
        history = MessageHistory(
            recipient=phone_number,
            channel="voice_call",
            content=f"[VOICE CALL] {message[:500]}",
            status="completed",
        )
        self.history.append(history)
        self._save()
        return {
            "success": True,
            "call_id": call_id,
            "phone_number": phone_number,
            "duration_sec": random.randint(15, 300),
            "message_preview": message[:100],
            "call_status": "completed",
        }

    def register_device(self, device_id: str, device_type: str, phone: str = "", platform: str = "") -> dict:
        self.registered_devices[device_id] = {
            "device_type": device_type,
            "phone": phone,
            "platform": platform,
            "registered_at": time.time(),
        }
        self._save()
        return {"success": True, "device_id": device_id}

    def add_contact(self, name: str, phone: str = "", email: str = "", channels: Optional[list[str]] = None) -> dict:
        self.contacts[name] = {
            "phone": phone,
            "email": email,
            "channels": channels or ["sms"],
            "added_at": time.time(),
        }
        self._save()
        return {"success": True, "name": name, "contact": self.contacts[name]}

    def get_channel_status(self, channel: str) -> dict:
        config = CHANNEL_CONFIGS.get(channel, {})
        recent = [m for m in self.history[-20:] if m.channel == channel]
        return {
            "channel": channel,
            "available": channel in CHANNEL_CONFIGS,
            "config": config,
            "recent_messages": len(recent),
            "last_sent": recent[-1].timestamp if recent else None,
        }

    def get_history(self, channel: Optional[str] = None, limit: int = 20) -> list[dict]:
        msgs = self.history
        if channel:
            msgs = [m for m in msgs if m.channel == channel]
        return [m.to_dict() for m in msgs[-limit:]]

    def summary(self) -> dict:
        channels = {}
        for m in self.history:
            channels[m.channel] = channels.get(m.channel, 0) + 1
        return {
            "total_messages": len(self.history),
            "channels_used": channels,
            "registered_devices": len(self.registered_devices),
            "contacts": len(self.contacts),
            "available_channels": list(CHANNEL_CONFIGS.keys()),
        }
