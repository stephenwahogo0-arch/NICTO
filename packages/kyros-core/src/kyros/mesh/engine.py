from enum import Enum
from uuid import uuid4
from datetime import datetime


class NodeStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"


class MeshNode:
    def __init__(self, name: str, address: str = "127.0.0.1"):
        self.id = str(uuid4())[:12]
        self.name = name
        self.address = address
        self.status = NodeStatus.ONLINE


class MeshConfig:
    def __init__(self, max_nodes: int = 100, heartbeat_interval: int = 30):
        self.max_nodes = max_nodes
        self.heartbeat_interval = heartbeat_interval


class MeshEngine:
    def __init__(self, config: MeshConfig = None):
        self.config = config or MeshConfig()
        self._nodes = {}
        self._tasks = {}
        self.running = False
        self.engine_id = str(uuid4())[:12]

    def add_node(self, name: str, address: str = "127.0.0.1") -> dict:
        node = MeshNode(name, address)
        self._nodes[node.id] = node
        return {"success": True, "node_id": node.id, "name": name, "address": address}

    def list_nodes(self) -> list[dict]:
        return [{"id": n.id, "name": n.name, "address": n.address, "status": n.status.value} for n in self._nodes.values()]

    async def start(self) -> dict:
        self.running = True
        return {"success": True, "status": "running", "engine_id": self.engine_id}

    async def stop(self) -> dict:
        self.running = False
        return {"success": True, "status": "stopped"}

    def submit_task(self, task_name: str, payload: dict = None) -> str:
        task_id = str(uuid4())[:12]
        self._tasks[task_id] = {"id": task_id, "name": task_name, "payload": payload or {}, "status": "queued", "created_at": datetime.now().isoformat()}
        return task_id
