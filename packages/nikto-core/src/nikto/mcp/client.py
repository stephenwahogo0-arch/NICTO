import asyncio
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(self, server_name: str):
        from nikto.mcp.registry import mcp_registry
        self.server = mcp_registry.get(server_name)
        if not self.server:
            raise ValueError(f"MCP server '{server_name}' not registered")

    async def call_tool(self, tool_name: str, arguments: dict = None) -> dict:
        if not self.server or not self.server.process:
            return {"error": "MCP server not running"}
        if not self.server.process.stdout or not self.server.process.stdin:
            return {"error": "MCP server stdio not available"}

        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments or {}},
        }
        try:
            self.server.process.stdin.write((json.dumps(request) + "\n").encode())
            await self.server.process.stdin.drain()
            line = await asyncio.wait_for(
                self.server.process.stdout.readline(), timeout=30
            )
            return json.loads(line.decode())
        except asyncio.TimeoutError:
            return {"error": "MCP call timed out"}
        except Exception as e:
            return {"error": str(e)}

    async def list_tools(self) -> list:
        if not self.server or not self.server.process:
            return []
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }
        try:
            self.server.process.stdin.write((json.dumps(request) + "\n").encode())
            await self.server.process.stdin.drain()
            line = await asyncio.wait_for(
                self.server.process.stdout.readline(), timeout=15
            )
            resp = json.loads(line.decode())
            return resp.get("result", {}).get("tools", [])
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            return []
