"""MCP (Model Context Protocol) server ecosystem for NIKTO.
Registers, starts, stops, and proxies MCP servers to the agent runtime."""
from nikto.mcp.server import MCPServer, MCPServerConfig, ServerStatus
from nikto.mcp.registry import MCPRegistry, mcp_registry
from nikto.mcp.client import MCPClient

__all__ = ["MCPServer", "MCPServerConfig", "ServerStatus", "MCPRegistry", "mcp_registry", "MCPClient"]
