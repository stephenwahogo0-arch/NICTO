"""Capability-based permission manager."""


class PermissionManager:
    """Manages capabilities and permissions for NICTO operations."""

    DEFAULT_CAPABILITIES = {
        "read_memory": True,
        "write_memory": True,
        "execute_tool": True,
        "train_model": True,
        "deploy": False,
        "delete_memory": False,
        "system_exec": False,
        "network_access": False,
    }

    def __init__(self):
        self._capabilities = dict(self.DEFAULT_CAPABILITIES)
        self._overrides: dict[str, bool] = {}
        self._audit_log: list[dict] = []

    def check(self, capability: str) -> bool:
        if capability in self._overrides:
            return self._overrides[capability]
        return self._capabilities.get(capability, False)

    def grant(self, capability: str, reason: str = "") -> None:
        self._overrides[capability] = True
        self._audit_log.append({
            "action": "grant",
            "capability": capability,
            "reason": reason,
        })

    def revoke(self, capability: str, reason: str = "") -> None:
        self._overrides[capability] = False
        self._audit_log.append({
            "action": "revoke",
            "capability": capability,
            "reason": reason,
        })

    def require(self, capability: str) -> None:
        """Raise if capability is not granted."""
        if not self.check(capability):
            raise PermissionError(f"Capability '{capability}' not granted")

    def list_capabilities(self) -> dict:
        merged = dict(self._capabilities)
        merged.update(self._overrides)
        return merged

    def get_audit_log(self, limit: int = 50) -> list[dict]:
        return self._audit_log[-limit:]
