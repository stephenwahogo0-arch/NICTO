from uuid import uuid4


class MCPSecureSandbox:
    def __init__(self, allowed_actions: list[str] = None):
        self.sandbox_id = str(uuid4())[:12]
        self.allowed_actions = allowed_actions or ["read", "list", "search"]
        self.execution_log = []

    async def execute_safe(self, action: str, params: dict = None) -> dict:
        if action not in self.allowed_actions:
            return {"success": False, "error": f"Action '{action}' not in sandbox allowlist"}
        self.execution_log.append({"action": action, "params": params})
        return {"success": True, "action": action, "sandbox_id": self.sandbox_id, "result": f"Executed {action} in sandbox"}
