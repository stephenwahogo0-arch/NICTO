import hashlib
import json
import os
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class AuditEntry:
    id: str
    actor: str
    action: str
    result: str
    state_hash: str
    prev_hash: str
    timestamp: float
    metadata: Dict = field(default_factory=dict)


class AuditLogger:
    def __init__(self, log_dir: str = None):
        self.log_dir = log_dir or os.path.join(os.path.expanduser("~"), ".nicto", "neural", "audit")
        os.makedirs(self.log_dir, exist_ok=True)
        self._entries: List[AuditEntry] = []
        self._load()

    def log_action(self, actor: str, action: str, result: Any, state_hash: str = None, metadata: Dict = None):
        prev_hash = self._entries[-1].state_hash if self._entries else "GENESIS"
        entry_id = f"audit_{int(time.time() * 1000000)}_{len(self._entries)}"
        entry = AuditEntry(
            id=entry_id,
            actor=actor,
            action=action,
            result=str(result)[:200],
            state_hash=state_hash or f"hash_{len(self._entries)}",
            prev_hash=prev_hash,
            timestamp=time.time(),
            metadata=metadata or {},
        )
        entry.state_hash = self._compute_hash(entry)
        self._entries.append(entry)
        self._append_to_disk(entry)
        return entry_id

    def get_logs(self, filter: Dict = None, limit: int = 100) -> List[Dict]:
        entries = self._entries
        if filter:
            for key, value in filter.items():
                entries = [e for e in entries if hasattr(e, key) and getattr(e, key) == value]
        return [{"id": e.id, "actor": e.actor, "action": e.action, "timestamp": e.timestamp} for e in entries[-limit:]]

    def verify_integrity(self) -> bool:
        if not self._entries:
            return True
        prev_hash = "GENESIS"
        for entry in self._entries:
            if entry.prev_hash != prev_hash:
                return False
            computed = self._compute_hash(entry)
            if computed != entry.state_hash:
                return False
            prev_hash = entry.state_hash
        return True

    def _compute_hash(self, entry: AuditEntry) -> str:
        data = f"{entry.id}|{entry.actor}|{entry.action}|{entry.result}|{entry.prev_hash}|{entry.timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _append_to_disk(self, entry: AuditEntry):
        path = os.path.join(self.log_dir, f"{entry.id}.json")
        with open(path, "w") as f:
            json.dump({
                "id": entry.id,
                "actor": entry.actor,
                "action": entry.action,
                "result": entry.result,
                "state_hash": entry.state_hash,
                "prev_hash": entry.prev_hash,
                "timestamp": entry.timestamp,
            }, f)

    def _load(self):
        if not os.path.exists(self.log_dir):
            return
        files = sorted([f for f in os.listdir(self.log_dir) if f.endswith(".json")])
        for fname in files:
            path = os.path.join(self.log_dir, fname)
            with open(path) as f:
                data = json.load(f)
            self._entries.append(AuditEntry(**data))