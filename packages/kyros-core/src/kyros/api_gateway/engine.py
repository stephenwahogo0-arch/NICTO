import hashlib
import json
import random
import secrets
import string
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


def generate_api_key(prefix: str = "nk") -> str:
    random_bytes = secrets.token_bytes(32)
    key_body = hashlib.sha256(random_bytes + str(time.time()).encode()).hexdigest()[:48]
    return f"{prefix}-{key_body[:8]}-{key_body[8:20]}-{key_body[20:32]}-{key_body[32:48]}"


def generate_key_secret() -> str:
    return secrets.token_hex(32)


@dataclass
class APIKey:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    key: str = ""
    name: str = ""
    secret: str = ""
    scope: str = "full_access"
    rate_limit: int = 1000
    usage_count: int = 0
    total_tokens: int = 0
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "key": self.key, "name": self.name,
            "scope": self.scope, "rate_limit": self.rate_limit,
            "usage_count": self.usage_count, "total_tokens": self.total_tokens,
            "is_active": self.is_active, "created_at": self.created_at,
            "expires_at": self.expires_at, "metadata": self.metadata,
        }


KEY_SCOPES = {
    "full_access": "Unrestricted access to all KYROS capabilities, tools, and data",
    "read_only": "Read-only access — query knowledge, search, retrieve context only",
    "execution": "Can execute tools and commands but cannot modify system configuration",
    "api_only": "Can only access API endpoints, no direct tool execution",
    "custom": "User-defined scope with specific capability restrictions",
}


class APIGateway:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.nikto").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.data_dir / "api_keys.json"
        self.keys: dict[str, APIKey] = {}
        self._load()

    def _load(self):
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text())
                for kid, kdata in data.items():
                    self.keys[kid] = APIKey(**kdata)
            except Exception:
                pass

    def _save(self):
        data = {kid: k.to_dict() for kid, k in self.keys.items()}
        self.store_path.write_text(json.dumps(data, indent=2))

    def create_key(self, name: str = "default", scope: str = "full_access", rate_limit: int = 1000) -> dict:
        if scope not in KEY_SCOPES:
            return {"success": False, "error": f"Invalid scope: {scope}. Valid: {list(KEY_SCOPES.keys())}"}

        api_key = APIKey(
            key=generate_api_key(),
            name=name,
            secret=generate_key_secret(),
            scope=scope,
            rate_limit=rate_limit,
        )
        self.keys[api_key.id] = api_key
        self._save()
        return {
            "success": True,
            "api_key": api_key.key,
            "api_secret": api_key.secret,
            "key_id": api_key.id,
            "name": api_key.name,
            "scope": api_key.scope,
            "scope_description": KEY_SCOPES[scope],
            "rate_limit_per_hour": api_key.rate_limit,
            "created_at": api_key.created_at,
            "instructions": f"Use this API key with any OpenAI-compatible client by setting base_url to your KYROS endpoint and api_key to '{api_key.key}'",
        }

    def validate_key(self, key: str) -> dict:
        for kid, k in self.keys.items():
            if k.key == key:
                if not k.is_active:
                    return {"valid": False, "error": "API key is deactivated"}
                if k.expires_at and time.time() > k.expires_at:
                    return {"valid": False, "error": "API key has expired"}
                if k.usage_count >= k.rate_limit:
                    return {"valid": False, "error": "Rate limit exceeded"}
                k.usage_count += 1
                self._save()
                return {
                    "valid": True,
                    "key_id": k.id,
                    "scope": k.scope,
                    "name": k.name,
                    "usage_remaining": k.rate_limit - k.usage_count,
                }
        return {"valid": False, "error": "Invalid API key"}

    def revoke_key(self, key_id: str) -> dict:
        if key_id not in self.keys:
            return {"success": False, "error": "Key not found"}
        self.keys[key_id].is_active = False
        self._save()
        return {"success": True, "key_id": key_id, "status": "revoked"}

    def list_keys(self) -> list[dict]:
        return [k.to_dict() for k in self.keys.values()]

    def get_usage_stats(self, key_id: Optional[str] = None) -> dict:
        if key_id:
            if key_id not in self.keys:
                return {"success": False, "error": "Key not found"}
            k = self.keys[key_id]
            return {"success": True, "key": k.to_dict()}
        total_keys = len(self.keys)
        active_keys = sum(1 for k in self.keys.values() if k.is_active)
        total_usage = sum(k.usage_count for k in self.keys.values())
        total_tokens = sum(k.total_tokens for k in self.keys.values())
        return {
            "success": True,
            "total_keys": total_keys,
            "active_keys": active_keys,
            "total_api_calls": total_usage,
            "total_tokens_processed": total_tokens,
        }

    def track_usage(self, key: str, tokens: int = 0):
        for k in self.keys.values():
            if k.key == key:
                k.total_tokens += tokens
                break
        self._save()

    def generate_self_api_key(self) -> dict:
        result = self.create_key(name="KYROS_SELF_GENERATED", scope="full_access", rate_limit=100000)
        result["message"] = "KYROS has generated its own API key — use this to connect KYROS to any external service, space, or application"
        result["example_usage"] = {
            "openai_compatible": f"base_url=http://localhost:8080/v1, api_key={result.get('api_key', '')}",
            "curl": f"curl http://localhost:8080/v1/chat/completions -H 'Authorization: Bearer {result.get('api_key', '')}' -d '{{\"model\":\"nikto\",\"messages\":[{{\"role\":\"user\",\"content\":\"Hello\"}}]}}'",
        }
        return result

    def summary(self) -> dict:
        scopes = {}
        for k in self.keys.values():
            scopes[k.scope] = scopes.get(k.scope, 0) + 1
        return {
            "total_keys": len(self.keys),
            "active_keys": sum(1 for k in self.keys.values() if k.is_active),
            "by_scope": scopes,
            "total_api_calls": sum(k.usage_count for k in self.keys.values()),
            "available_scopes": list(KEY_SCOPES.keys()),
        }
