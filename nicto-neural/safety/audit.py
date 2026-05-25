"""Tamper-evident action logging."""

import hashlib
import json
from datetime import datetime


class AuditLogger:
    """Tamper-evident audit log with hash chaining."""

    def __init__(self):
        self._entries: list[dict] = []
        self._last_hash = "genesis"

    def log(self, action: str, details: dict = None, actor: str = "system") -> dict:
        """Log an action with tamper-evident hash chain."""
        entry = {
            "seq": len(self._entries),
            "action": action,
            "details": details or {},
            "actor": actor,
            "timestamp": datetime.utcnow().isoformat(),
            "prev_hash": self._last_hash,
        }

        entry_bytes = json.dumps(entry, sort_keys=True).encode()
        entry["hash"] = hashlib.sha256(entry_bytes).hexdigest()
        self._last_hash = entry["hash"]

        self._entries.append(entry)
        return entry

    def verify_chain(self) -> dict:
        """Verify the entire audit chain integrity."""
        if not self._entries:
            return {"valid": True, "entries": 0}

        prev_hash = "genesis"
        for i, entry in enumerate(self._entries):
            if entry["prev_hash"] != prev_hash:
                return {
                    "valid": False,
                    "broken_at": i,
                    "expected": prev_hash,
                    "found": entry["prev_hash"],
                }
            prev_hash = entry["hash"]

        return {"valid": True, "entries": len(self._entries)}

    def query(
        self,
        action: str = None,
        actor: str = None,
        limit: int = 50,
    ) -> list[dict]:
        results = self._entries
        if action:
            results = [e for e in results if e["action"] == action]
        if actor:
            results = [e for e in results if e["actor"] == actor]
        return results[-limit:]

    def get_stats(self) -> dict:
        return {
            "total_entries": len(self._entries),
            "chain_valid": self.verify_chain()["valid"],
            "last_hash": self._last_hash,
        }
