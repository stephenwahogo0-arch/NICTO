"""
Nikto API Key Management — generate, validate, revoke, and manage API keys.

Provides a NiktoKeyManager that can generate API keys (like `nk-...`)
for external agents and users to authenticate against the Nikto system.
Inspired by Anthropic (sk-ant-...) and OpenAI (sk-...) key formats.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


KEY_PREFIX = "nk-"
KEY_BYTES = 32
_KEY_DIR = Path.home() / ".nikto"
_KEY_FILE = _KEY_DIR / "api_keys.json"


@dataclass
class StoredKey:
    prefix: str
    hash: str
    name: str
    created_at: str
    expires_at: Optional[str]
    owner: str
    enabled: bool
    last_used: Optional[str]
    scopes: list[str]
    usage_count: int


def _ensure_dir() -> None:
    _KEY_DIR.mkdir(parents=True, exist_ok=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _verify_key(raw: str, stored_hash: str) -> bool:
    return hmac.compare_digest(_hash_key(raw), stored_hash)


def _load_all() -> dict[str, StoredKey]:
    if not _KEY_FILE.exists():
        return {}
    try:
        with open(_KEY_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        return {k: StoredKey(**v) for k, v in raw.items()}
    except (json.JSONDecodeError, OSError, TypeError):
        return {}


def _save_all(keys: dict[str, StoredKey]) -> None:
    _ensure_dir()
    serializable = {k: asdict(v) for k, v in keys.items()}
    with open(_KEY_FILE, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=2)


class NiktoKeyManager:
    """
    Manages Nikto's own API keys that users/agents can use to access the system.

    Usage:
        mgr = NiktoKeyManager()
        key = mgr.generate_key("My Agent", scopes=["chat", "scan"])
        mgr.validate_key(key)  # -> True
        mgr.revoke_key(key)     # -> True
    """

    def __init__(self) -> None:
        self._keys: dict[str, StoredKey] = _load_all()

    def generate_key(
        self,
        name: str,
        *,
        owner: str = "default",
        scopes: Optional[list[str]] = None,
        expires_in_days: Optional[int] = None,
    ) -> tuple[str, StoredKey]:
        """
        Generate a new API key.

        Returns (raw_key, stored_record).
        The raw key is shown ONCE at creation — it will not be stored in plaintext.
        """
        raw = secrets.token_urlsafe(KEY_BYTES)
        raw_key = f"{KEY_PREFIX}{raw}"
        key_hash = _hash_key(raw_key)
        prefix_short = raw_key[:12]

        expires_at: Optional[str] = None
        if expires_in_days is not None:
            expiry = datetime.now(timezone.utc).timestamp() + expires_in_days * 86400
            expires_at = datetime.fromtimestamp(expiry, timezone.utc).isoformat()

        record = StoredKey(
            prefix=prefix_short,
            hash=key_hash,
            name=name,
            created_at=_now_iso(),
            expires_at=expires_at,
            owner=owner,
            enabled=True,
            last_used=None,
            scopes=sorted(scopes) if scopes else [],
            usage_count=0,
        )

        self._keys[prefix_short] = record
        _save_all(self._keys)
        return raw_key, record

    def validate_key(self, raw_key: str) -> bool:
        """Check whether a raw API key is valid and enabled."""
        if not raw_key or not raw_key.startswith(KEY_PREFIX):
            return False

        for record in self._keys.values():
            if _verify_key(raw_key, record.hash):
                if not record.enabled:
                    return False
                if record.expires_at:
                    exp_ts = datetime.fromisoformat(record.expires_at).timestamp()
                    if time.time() > exp_ts:
                        return False
                self._touch_usage(record)
                return True
        return False

    def validate_key_with_record(self, raw_key: str) -> tuple[bool, Optional[StoredKey]]:
        """Validate a key and return the record if valid."""
        if not raw_key or not raw_key.startswith(KEY_PREFIX):
            return False, None

        for record in self._keys.values():
            if _verify_key(raw_key, record.hash):
                if not record.enabled:
                    return False, record
                if record.expires_at:
                    exp_ts = datetime.fromisoformat(record.expires_at).timestamp()
                    if time.time() > exp_ts:
                        return False, record
                self._touch_usage(record)
                return True, record
        return False, None

    def revoke_key(self, raw_key: str) -> bool:
        """Revoke (disable) an API key by its raw value or 12-char prefix."""
        prefix = raw_key[:12] if raw_key.startswith(KEY_PREFIX) else raw_key
        record = self._keys.get(prefix)
        if record is None:
            return False
        record.enabled = False
        _save_all(self._keys)
        return True

    def delete_key(self, raw_key: str) -> bool:
        """Permanently remove a key record."""
        prefix = raw_key[:12] if raw_key.startswith(KEY_PREFIX) else raw_key
        if prefix not in self._keys:
            return False
        del self._keys[prefix]
        _save_all(self._keys)
        return True

    def list_keys(self) -> list[dict]:
        """Return a list of all key records (safe — no raw secrets)."""
        return [
            {
                "prefix": v.prefix,
                "name": v.name,
                "created_at": v.created_at,
                "expires_at": v.expires_at,
                "owner": v.owner,
                "enabled": v.enabled,
                "last_used": v.last_used,
                "scopes": v.scopes,
                "usage_count": v.usage_count,
            }
            for v in self._keys.values()
        ]

    def get_key_info(self, prefix: str) -> Optional[dict]:
        """Get info about a specific key by its prefix."""
        record = self._keys.get(prefix)
        if not record:
            return None
        return {
            "prefix": record.prefix,
            "name": record.name,
            "created_at": record.created_at,
            "expires_at": record.expires_at,
            "owner": record.owner,
            "enabled": record.enabled,
            "last_used": record.last_used,
            "scopes": record.scopes,
            "usage_count": record.usage_count,
        }

    def reload(self) -> None:
        """Reload keys from disk (e.g., if another instance updated them)."""
        self._keys = _load_all()

    def _touch_usage(self, record: StoredKey) -> None:
        record.last_used = _now_iso()
        record.usage_count += 1
        _save_all(self._keys)
