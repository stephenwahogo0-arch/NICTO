import json
import logging
from pathlib import Path
from typing import Optional

from nikto.mcp.server import MCPServer, MCPServerConfig, ServerStatus

logger = logging.getLogger(__name__)


class MCPRegistry:
    def __init__(self):
        self._servers: dict[str, MCPServer] = {}
        self._config_file = Path.home() / ".nikto" / "mcp_servers.json"
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        if self._config_file.exists():
            try:
                data = json.loads(self._config_file.read_text())
                for entry in data:
                    cfg = MCPServerConfig(**entry)
                    self._servers[cfg.name] = MCPServer(config=cfg)
                logger.info(f"Loaded {len(data)} MCP servers from config")
            except Exception as e:
                logger.error(f"Failed to load MCP config: {e}")

    def _save(self):
        data = [s.config.__dict__ for s in self._servers.values()]
        self._config_file.write_text(json.dumps(data, indent=2, default=str))

    def register(self, name: str, command: str, args: list = None, env: dict = None,
                 port: int = 0, transport: str = "stdio", auto_start: bool = False,
                 description: str = "") -> MCPServer:
        cfg = MCPServerConfig(
            name=name, command=command, args=args or [],
            env=env or {}, port=port, transport=transport,
            auto_start=auto_start, description=description,
        )
        server = MCPServer(config=cfg)
        self._servers[name] = server
        self._save()
        logger.info(f"Registered MCP server: {name}")
        return server

    def unregister(self, name: str) -> bool:
        if name in self._servers:
            del self._servers[name]
            self._save()
            return True
        return False

    def get(self, name: str) -> Optional[MCPServer]:
        return self._servers.get(name)

    def list(self) -> list[dict]:
        return [s.to_dict() for s in self._servers.values()]

    def running(self) -> list[MCPServer]:
        return [s for s in self._servers.values() if s.status == ServerStatus.RUNNING]


mcp_registry = MCPRegistry()
