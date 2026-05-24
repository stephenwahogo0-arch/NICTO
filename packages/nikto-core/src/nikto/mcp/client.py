from nikto.mcp.registry import mcp_registry


class MCPClient:
    def __init__(self, server_name: str):
        self.server_name = server_name
        server = mcp_registry.get(server_name)
        if not server:
            raise ValueError(f"MCP server '{server_name}' not found in registry")
        self.server_info = server
