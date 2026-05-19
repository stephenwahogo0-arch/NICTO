"""Connection Manager — connects to email, workspaces, social accounts, and more."""

import json
import logging
import os
import smtplib
import ssl
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ConnectionType(str, Enum):
    EMAIL = "email"
    WORKSPACE = "workspace"
    SOCIAL = "social"
    GIT = "git"
    FILE_SYSTEM = "file_system"
    DATABASE = "database"
    API = "api"
    CRYPTO = "crypto"
    CUSTOM = "custom"


@dataclass
class Connection:
    name: str
    type: ConnectionType
    config: dict = field(default_factory=dict)
    connected: bool = False
    last_active: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type.value,
            "connected": self.connected,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "error": self.error,
        }


class ConnectionManager:
    """Manages all external connections for the autopilot."""

    def __init__(self, data_dir: str = "~/.nikto/autopilot"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.connections: dict[str, Connection] = {}

    async def auto_discover(self):
        """Auto-discover available connections on the system."""
        await self._discover_file_system()
        await self._discover_git()
        await self._discover_workspaces()
        logger.info(f"Auto-discovered {len(self.connections)} connections")

    async def _discover_file_system(self):
        self.add(Connection(
            name="local_fs",
            type=ConnectionType.FILE_SYSTEM,
            config={"root": str(Path.home())},
            connected=True,
            last_active=datetime.now(),
        ))

    async def _discover_git(self):
        try:
            import git
            repo = git.Repo(Path.cwd(), search_parent_directories=True)
            self.add(Connection(
                name="git_workspace",
                type=ConnectionType.GIT,
                config={"remote": [r.url for r in repo.remotes] if repo.remotes else [], "branch": repo.active_branch.name},
                connected=True,
                last_active=datetime.now(),
            ))
        except Exception:
            pass

    async def _discover_workspaces(self):
        home = Path.home()
        workspace_dirs = [
            home / "Desktop",
            home / "Documents",
            home / "Projects",
            home / "workspace",
            home / "code",
            Path.cwd(),
        ]
        found = []
        for d in workspace_dirs:
            if d.exists():
                found.append(str(d))
        if found:
            self.add(Connection(
                name="workspaces",
                type=ConnectionType.WORKSPACE,
                config={"directories": found},
                connected=True,
                last_active=datetime.now(),
            ))

    async def connect_email(self, email: str, password: str, smtp_host: str = "smtp.gmail.com", smtp_port: int = 587) -> bool:
        try:
            context = ssl.create_default_context()
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls(context=context)
            server.login(email, password)
            server.quit()
            self.add(Connection(
                name=f"email:{email}",
                type=ConnectionType.EMAIL,
                config={"email": email, "smtp_host": smtp_host, "smtp_port": smtp_port},
                connected=True,
                last_active=datetime.now(),
            ))
            return True
        except Exception as e:
            logger.error(f"Email connection failed: {e}")
            self.add(Connection(
                name=f"email:{email}",
                type=ConnectionType.EMAIL,
                config={"email": email},
                connected=False,
                error=str(e),
            ))
            return False

    async def connect_social(self, platform: str, token: str, username: str = "") -> bool:
        self.add(Connection(
            name=f"social:{platform}",
            type=ConnectionType.SOCIAL,
            config={"platform": platform, "username": username, "token_prefix": token[:8] + "..."},
            connected=True,
            last_active=datetime.now(),
        ))
        return True

    async def connect_api(self, name: str, base_url: str, api_key: str = "") -> bool:
        self.add(Connection(
            name=f"api:{name}",
            type=ConnectionType.API,
            config={"base_url": base_url},
            connected=True,
            last_active=datetime.now(),
        ))
        return True

    def add(self, connection: Connection):
        self.connections[connection.name] = connection

    def get(self, name: str) -> Optional[Connection]:
        return self.connections.get(name)

    def get_by_type(self, conn_type: ConnectionType) -> list[Connection]:
        return [c for c in self.connections.values() if c.type == conn_type]

    def count(self) -> int:
        return len(self.connections)

    def disconnect_all(self):
        for conn in self.connections.values():
            conn.connected = False
            conn.last_active = datetime.now()

    def list_all(self) -> list[dict]:
        return [c.to_dict() for c in self.connections.values()]
