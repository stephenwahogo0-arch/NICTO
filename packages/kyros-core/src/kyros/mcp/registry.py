from uuid import uuid4


class MCPRegistry:
    def __init__(self):
        self._servers = {}

    def register(self, name: str, server_info: dict) -> dict:
        server_id = str(uuid4())[:12]
        self._servers[name] = {"id": server_id, "name": name, **server_info}
        return {"success": True, "server_id": server_id, "name": name}

    def unregister(self, name: str) -> dict:
        if name in self._servers:
            del self._servers[name]
            return {"success": True, "name": name}
        return {"success": False, "error": f"Server '{name}' not found"}

    def get(self, name: str) -> dict:
        return self._servers.get(name)

    def list_servers(self) -> list[dict]:
        return list(self._servers.values())


mcp_registry = MCPRegistry()
