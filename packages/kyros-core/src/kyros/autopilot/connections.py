from enum import Enum
from uuid import uuid4
from datetime import datetime


class ConnectionType(Enum):
    SSH = "ssh"
    API = "api"
    DOCKER = "docker"
    MQTT = "mqtt"
    BLUETOOTH = "bluetooth"


class Connection:
    def __init__(self, name: str, conn_type: ConnectionType, config: dict = None):
        self.id = str(uuid4())[:12]
        self.name = name
        self.conn_type = conn_type
        self.config = config or {}
        self.created_at = datetime.now().isoformat()


class ConnectionManager:
    def __init__(self):
        self._connections = {}

    def add(self, name: str, conn_type: ConnectionType, config: dict = None) -> dict:
        conn = Connection(name, conn_type, config)
        self._connections[conn.id] = conn
        return {"success": True, "id": conn.id, "name": name, "type": conn_type.value}

    def count(self) -> int:
        return len(self._connections)

    def list_connections(self) -> list[dict]:
        return [{"id": c.id, "name": c.name, "type": c.conn_type.value} for c in self._connections.values()]
