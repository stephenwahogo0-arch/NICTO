import asyncio
import enum
import json
import logging
import socket
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ServerStatus(enum.Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: list = field(default_factory=list)
    env: dict = field(default_factory=dict)
    port: int = 0
    transport: str = "stdio"  # stdio, sse, websocket
    auto_start: bool = False
    description: str = ""


@dataclass
class MCPServer:
    config: MCPServerConfig
    status: ServerStatus = ServerStatus.STOPPED
    process: Optional[subprocess.Popen] = None
    started_at: Optional[datetime] = None
    pid: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.config.name,
            "status": self.status.value,
            "pid": self.pid,
            "transport": self.config.transport,
            "port": self.config.port,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "description": self.config.description,
        }

    async def start(self):
        if self.status == ServerStatus.RUNNING:
            return
        self.status = ServerStatus.STARTING
        self.started_at = datetime.utcnow()
        try:
            env = {**dict(self.config.env)}
            self.process = await asyncio.create_subprocess_exec(
                self.config.command, *self.config.args,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self.pid = self.process.pid
            self.status = ServerStatus.RUNNING
            logger.info(f"MCP server '{self.config.name}' started (PID {self.pid})")
        except Exception as e:
            self.status = ServerStatus.ERROR
            logger.error(f"Failed to start MCP server '{self.config.name}': {e}")

    async def stop(self):
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=10)
            except asyncio.TimeoutError:
                self.process.kill()
            self.process = None
        self.status = ServerStatus.STOPPED
        logger.info(f"MCP server '{self.config.name}' stopped")
