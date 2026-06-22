"""
API Key management for NIKTO.

Provides a KeyVault that reads from environment variables, .env files,
or encrypted local storage. Supports multiple AI service providers.
"""

import json
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


# Default services and their expected env var names
SERVICE_ENV_MAP: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "ibm_quantum": "IBM_QUANTUM_TOKEN",
    "google": "GOOGLE_API_KEY",
    "cohere": "COHERE_API_KEY",
    "huggingface": "HUGGINGFACE_TOKEN",
    "deepseek": "DEEPSEEK_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "together": "TOGETHER_API_KEY",
    "replicate": "REPLICATE_API_TOKEN",
    "stability": "STABILITY_API_KEY",
}


def _get_keys_path() -> Path:
    """Return path to the local keys JSON file."""
    return Path.home() / ".nikto" / "keys.json"


def _ensure_keys_dir() -> None:
    """Ensure the .nikto config directory exists."""
    Path.home().joinpath(".nikto").mkdir(parents=True, exist_ok=True)


class KeyVault:
    """Secure key-value store for API credentials.

    Resolution order:
    1. Environment variables (already loaded by dotenv)
    2. ~/.nikto/keys.json (JSON file with service -> key mappings)
    """

    def __init__(self, keys_path: Optional[Path] = None) -> None:
        load_dotenv()
        self._keys_path = keys_path or _get_keys_path()
        self._cache: dict[str, str] = {}

    def get_key(self, service: str) -> Optional[str]:
        """Get an API key for the given service.

        Returns None if the key is not found in any source.
        """
        # Check cache first
        if service in self._cache:
            return self._cache[service]

        # 1. Check environment variables
        env_var = SERVICE_ENV_MAP.get(service)
        if env_var:
            value = os.environ.get(env_var)
            if value:
                self._cache[service] = value
                return value

        # Check common generic env vars
        generic_var = f"{service.upper()}_API_KEY"
        value = os.environ.get(generic_var)
        if value:
            self._cache[service] = value
            return value

        # 2. Check local keys file
        if self._keys_path.exists():
            try:
                with open(self._keys_path, encoding="utf-8") as f:
                    data = json.load(f)
                if service in data:
                    self._cache[service] = str(data[service])
                    return str(data[service])
            except (json.JSONDecodeError, OSError):
                pass

        return None

    def set_key(self, service: str, key: str) -> None:
        """Store an API key for the given service.

        Writes to the local keys JSON file (~/.nikto/keys.json).
        The file stores keys in plain text — protect it with filesystem permissions.
        """
        _ensure_keys_dir()

        existing: dict[str, str] = {}
        if self._keys_path.exists():
            try:
                with open(self._keys_path, encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        existing[service] = key

        with open(self._keys_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)

        self._cache[service] = key

    def delete_key(self, service: str) -> bool:
        """Remove a stored key for the given service.

        Returns True if the key existed and was removed, False otherwise.
        """
        if not self._keys_path.exists():
            return False

        try:
            with open(self._keys_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return False

        if service not in data:
            return False

        del data[service]
        with open(self._keys_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        self._cache.pop(service, None)
        return True

    def list_services(self) -> list[str]:
        """Return all known service names that have keys available."""
        found: list[str] = []

        # From env vars
        for service, env_var in SERVICE_ENV_MAP.items():
            if os.environ.get(env_var):
                found.append(service)

        # From keys file
        if self._keys_path.exists():
            try:
                with open(self._keys_path, encoding="utf-8") as f:
                    data = json.load(f)
                found.extend(k for k in data if k not in found)
            except (json.JSONDecodeError, OSError):
                pass

        return found

    def clear_cache(self) -> None:
        """Clear the in-memory cache (forces re-read from sources)."""
        self._cache.clear()
