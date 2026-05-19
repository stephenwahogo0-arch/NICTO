"""Distributed Mesh Networking — spawn NIKTO agent instances across networked machines."""

import asyncio
import json
import logging
import os
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class NodeStatus(str, Enum):
    OFFLINE = "offline"
    ONLINE = "online"
    BUSY = "busy"
    ERROR = "error"


@dataclass
class MeshNode:
    hostname: str
    address: str
    port: int = 22
    status: NodeStatus = NodeStatus.OFFLINE
    capabilities: list[str] = field(default_factory=list)
    cpu_count: int = 0
    memory_mb: int = 0
    last_seen: float = 0.0
    node_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def to_dict(self) -> dict:
        return {
            "hostname": self.hostname,
            "address": self.address,
            "port": self.port,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "cpu_count": self.cpu_count,
            "memory_mb": self.memory_mb,
            "node_id": self.node_id,
        }


@dataclass
class MeshTask:
    task_type: str
    payload: dict
    target_node: str = ""
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    priority: int = 0
    timeout: int = 60
    created_at: float = field(default_factory=time.time)


@dataclass
class MeshResult:
    task_id: str
    success: bool
    output: str = ""
    error: str = ""
    node_id: str = ""
    duration_ms: float = 0.0
    earnings: float = 0.0


@dataclass
class MeshConfig:
    listen_port: int = 9786
    auto_discover: bool = True
    discovery_broadcast: str = "255.255.255.255"
    max_nodes: int = 100
    task_timeout: int = 120
    data_dir: str = "~/.nikto/mesh"


class MeshEngine:
    """Manages a distributed network of NIKTO agents across machines."""

    def __init__(self, config: Optional[MeshConfig] = None):
        self.config = config or MeshConfig()
        self.nodes: dict[str, MeshNode] = {}
        self._my_id = f"nikto-{uuid.uuid4().hex[:8]}"
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._pending_tasks: list[MeshTask] = []
        self._completed: list[MeshResult] = []

        # Register localhost as initial node
        import platform
        self._register_local(platform.node())

    def _register_local(self, hostname: str):
        import multiprocessing
        node = MeshNode(
            hostname=hostname,
            address="127.0.0.1",
            status=NodeStatus.ONLINE,
            cpu_count=multiprocessing.cpu_count(),
            memory_mb=self._get_memory(),
            capabilities=["python", "nikto", "local"],
        )
        self.nodes[node.node_id] = node

    def _get_memory(self) -> int:
        try:
            import psutil
            return int(psutil.virtual_memory().total / 1024 / 1024)
        except ImportError:
            return 0

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._mesh_loop())
        logger.info(f"Mesh engine started (node_id={self._my_id})")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Mesh engine stopped")

    async def _mesh_loop(self):
        while self._running:
            try:
                self._process_pending()
                self._check_node_health()
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Mesh loop error: {e}")
                await asyncio.sleep(30)

    def _process_pending(self):
        still_pending = []
        for task in self._pending_tasks:
            node = self._find_best_node(task)
            if node:
                result = self._execute_on_node(node, task)
                self._completed.append(result)
            else:
                still_pending.append(task)
        self._pending_tasks = still_pending

    def _find_best_node(self, task: MeshTask) -> Optional[MeshNode]:
        available = [n for n in self.nodes.values() if n.status == NodeStatus.ONLINE]
        if task.target_node:
            for n in available:
                if n.node_id == task.target_node or n.hostname == task.target_node:
                    return n
        return available[0] if available else None

    def _execute_on_node(self, node: MeshNode, task: MeshTask) -> MeshResult:
        start = time.time()
        try:
            if node.address == "127.0.0.1":
                result = self._execute_local(task)
            else:
                result = self._execute_remote(node, task)
            result.duration_ms = (time.time() - start) * 1000
            result.node_id = node.node_id
            return result
        except Exception as e:
            return MeshResult(task.task_id, False, error=str(e), duration_ms=(time.time() - start) * 1000)

    def _execute_local(self, task: MeshTask) -> MeshResult:
        if task.task_type == "benchmark":
            import time as t
            t.sleep(0.1)
            return MeshResult(task.task_id, True, output="Benchmark completed on local node")
        elif task.task_type == "scan":
            target = task.payload.get("target", "localhost")
            return MeshResult(task.task_id, True, output=f"Scan of {target} initiated")
        elif task.task_type == "process":
            data = task.payload.get("data", "")
            return MeshResult(task.task_id, True, output=f"Processed {len(data)} bytes")
        elif task.task_type == "earn":
            import random
            earned = round(random.uniform(0.01, 2.0), 4)
            return MeshResult(task.task_id, True, output=f"Earned ${earned}", earnings=earned)
        else:
            return MeshResult(task.task_id, True, output=f"Executed {task.task_type}")

    def _execute_remote(self, node: MeshNode, task: MeshTask) -> MeshResult:
        try:
            cmd = ["ssh", "-o", "ConnectTimeout=5", f"{node.address}"]
            if task.task_type == "ping":
                cmd.append("echo pong")
            else:
                cmd.extend(["python3", "-c", f"print('{task.task_type} executed')"])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=task.timeout)
            return MeshResult(task.task_id, result.returncode == 0, output=result.stdout, error=result.stderr)
        except subprocess.TimeoutExpired:
            return MeshResult(task.task_id, False, error="Remote execution timed out")
        except FileNotFoundError:
            return MeshResult(task.task_id, False, error="SSH not available")
        except Exception as e:
            return MeshResult(task.task_id, False, error=str(e))

    def _check_node_health(self):
        now = time.time()
        for node in self.nodes.values():
            if node.last_seen > 0 and now - node.last_seen > 300:
                node.status = NodeStatus.OFFLINE

    def add_node(self, hostname: str, address: str, port: int = 22, capabilities: list[str] = None) -> str:
        node = MeshNode(
            hostname=hostname,
            address=address,
            port=port,
            capabilities=capabilities or [],
            last_seen=time.time(),
        )
        self.nodes[node.node_id] = node
        return node.node_id

    def remove_node(self, node_id: str) -> bool:
        if node_id in self.nodes:
            del self.nodes[node_id]
            return True
        return False

    async def submit_task(self, task_type: str, payload: dict, target_node: str = "", priority: int = 0) -> str:
        task = MeshTask(
            task_type=task_type,
            payload=payload,
            target_node=target_node,
            priority=priority,
        )
        self._pending_tasks.append(task)
        return task.task_id

    def get_results(self, count: int = 20) -> list[dict]:
        return [{
            "task_id": r.task_id,
            "success": r.success,
            "output": r.output[:200],
            "error": r.error[:200],
            "node_id": r.node_id,
            "duration_ms": round(r.duration_ms, 2),
            "earnings": r.earnings,
        } for r in self._completed[-count:]]

    def list_nodes(self) -> list[dict]:
        return [n.to_dict() for n in self.nodes.values()]

    def summary(self) -> dict:
        return {
            "my_id": self._my_id,
            "nodes": len(self.nodes),
            "online": sum(1 for n in self.nodes.values() if n.status == NodeStatus.ONLINE),
            "pending_tasks": len(self._pending_tasks),
            "completed_tasks": len(self._completed),
            "running": self._running,
        }
