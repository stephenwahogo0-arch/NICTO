"""NICTO X — Authentication and authorization system."""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("nicto_x.security")


@dataclass
class Token:
    key: str = ""
    owner: str = ""
    scopes: list[str] = field(default_factory=lambda: ["read"])
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    enabled: bool = True


class AuthManager:
    """Manages API tokens, authentication, and audit logging."""

    def __init__(self, store_path: str = ""):
        self._path = Path(store_path or Path.home() / ".nicto-x" / "auth.json")
        self._tokens: dict[str, Token] = {}
        self._audit_log: list[dict] = []
        self._load()

    def create_token(self, owner: str, scopes: Optional[list[str]] = None, expire_hours: int = 0) -> str:
        raw = f"nx-{secrets.token_urlsafe(32)}"
        token = Token(
            key=hashlib.sha256(raw.encode()).hexdigest(),
            owner=owner,
            scopes=scopes or ["read"],
            expires_at=time.time() + expire_hours * 3600 if expire_hours > 0 else None,
        )
        self._tokens[token.key] = token
        self._save()
        return raw

    def validate(self, raw_key: str, required_scope: str = "") -> bool:
        h = hashlib.sha256(raw_key.encode()).hexdigest()
        token = self._tokens.get(h)
        if not token or not token.enabled:
            self._audit("auth_failure", f"Invalid key: {raw_key[:12]}...")
            return False
        if token.expires_at and time.time() > token.expires_at:
            self._audit("auth_failure", f"Expired key: {raw_key[:12]}...")
            return False
        if required_scope and required_scope not in token.scopes:
            self._audit("auth_failure", f"Missing scope '{required_scope}'")
            return False
        self._audit("auth_success", f"Key validated: {raw_key[:12]}...")
        return True

    def revoke_token(self, raw_key: str) -> bool:
        h = hashlib.sha256(raw_key.encode()).hexdigest()
        token = self._tokens.get(h)
        if token:
            token.enabled = False
            self._save()
            return True
        return False

    def list_tokens(self) -> list[dict]:
        return [
            {
                "owner": t.owner,
                "scopes": t.scopes,
                "created": t.created_at,
                "expires": t.expires_at,
                "enabled": t.enabled,
            }
            for t in self._tokens.values()
        ]

    def get_audit_log(self, limit: int = 100) -> list[dict]:
        return self._audit_log[-limit:]

    def _audit(self, action: str, detail: str):
        self._audit_log.append({
            "action": action,
            "detail": detail,
            "timestamp": time.time(),
        })

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump({
                "tokens": {k: v.__dict__ for k, v in self._tokens.items()},
                "audit": self._audit_log[-1000:],
            }, f, indent=2)

    def _load(self):
        if self._path.exists():
            with open(self._path) as f:
                data = json.load(f)
            for k, v in data.get("tokens", {}).items():
                self._tokens[k] = Token(**v)
            self._audit_log = data.get("audit", [])
