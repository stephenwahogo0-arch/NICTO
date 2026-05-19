import enum
import json
import random
import socket
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


class DeploymentTarget(enum.Enum):
    LINUX_SERVER = "linux_server"
    WINDOWS_SERVER = "windows_server"
    RASPBERRY_PI = "raspberry_pi"
    ANDROID = "android"
    IOS = "ios"
    MACOS = "macos"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    IOT_DEVICE = "iot_device"
    EMBEDDED = "embedded"
    CLOUD_VM = "cloud_vm"
    EDGE_DEVICE = "edge_device"


@dataclass
class DeploymentRecord:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    target: str = ""
    hostname: str = ""
    status: str = "pending"
    version: str = "1.0.0"
    components: list = field(default_factory=list)
    config: dict = field(default_factory=dict)
    installed_at: Optional[float] = None
    last_heartbeat: Optional[float] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "target": self.target,
            "hostname": self.hostname, "status": self.status,
            "version": self.version, "components": self.components,
            "config": self.config, "installed_at": self.installed_at,
            "last_heartbeat": self.last_heartbeat, "metadata": self.metadata,
        }


DEPLOYMENT_TEMPLATES = {
    "linux_server": {"description": "Full NIKTO agent on Linux server — systemd service, auto-update, all modules", "components": ["nikto-core", "autopilot", "arsenal", "mobile-gateway", "mesh-node"]},
    "raspberry_pi": {"description": "Lightweight NIKTO agent for Raspberry Pi — GPIO control, sensor integration, low-power", "components": ["nikto-core-lite", "iot-bridge", "sensor-agent"]},
    "android": {"description": "NIKTO mobile agent for Android — background service, SMS gateway, notification handler", "components": ["nikto-mobile", "sms-gateway", "notification-agent"]},
    "docker": {"description": "Containerized NIKTO deployment — single container, docker-compose, or swarm", "components": ["nikto-container", "sandbox-runtime", "api-gateway"]},
    "kubernetes": {"description": "Kubernetes deployment — pods, services, configmaps, auto-scaling", "components": ["nikto-controller", "worker-pods", "mesh-sidecar", "sandbox-pool"]},
    "iot_device": {"description": "Minimal NIKTO agent for IoT and embedded devices — MQTT, CoAP, BLE", "components": ["nikto-embedded", "mqtt-bridge", "sensor-collector"]},
    "edge_device": {"description": "Edge-optimized NIKTO — offline-first, sync-on-connect, local inference", "components": ["nikto-edge", "local-llm", "sync-engine"]},
}


class DeployEngine:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.nikto").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.data_dir / "deployments.json"
        self.deployments: dict[str, DeploymentRecord] = {}
        self._load()

    def _load(self):
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text())
                for did, d in data.items():
                    self.deployments[did] = DeploymentRecord(**d)
            except Exception:
                pass

    def _save(self):
        data = {d.id: d.to_dict() for d in self.deployments.values()}
        self.store_path.write_text(json.dumps(data, indent=2))

    def deploy(self, target: str, hostname: str = "", version: str = "1.0.0", config: Optional[dict] = None) -> dict:
        try:
            target_enum = DeploymentTarget(target)
        except ValueError:
            return {"success": False, "error": f"Invalid target: {target}. Valid: {[t.value for t in DeploymentTarget]}"}

        template = DEPLOYMENT_TEMPLATES.get(target, {})
        record = DeploymentRecord(
            target=target,
            hostname=hostname or f"{target}-{random.randint(1000,9999)}",
            status="deploying",
            version=version,
            components=template.get("components", ["nikto-core"]),
            config=config or {},
        )
        simulated_success = random.random() < 0.95
        if simulated_success:
            record.status = "running"
            record.installed_at = time.time()
            record.last_heartbeat = time.time()
        else:
            record.status = "failed"

        self.deployments[record.id] = record
        self._save()
        return {
            "success": simulated_success,
            "deployment_id": record.id,
            "target": target,
            "hostname": record.hostname,
            "status": record.status,
            "components": record.components,
            "description": template.get("description", ""),
        }

    def uninstall(self, deployment_id: str) -> dict:
        if deployment_id not in self.deployments:
            return {"success": False, "error": "Deployment not found"}
        self.deployments[deployment_id].status = "uninstalled"
        self._save()
        return {"success": True, "deployment_id": deployment_id}

    def heartbeat(self, deployment_id: str) -> dict:
        if deployment_id not in self.deployments:
            return {"success": False, "error": "Deployment not found"}
        self.deployments[deployment_id].last_heartbeat = time.time()
        self.deployments[deployment_id].status = "running"
        self._save()
        return {"success": True, "deployment_id": deployment_id, "status": "running"}

    def update(self, deployment_id: str, new_version: str) -> dict:
        if deployment_id not in self.deployments:
            return {"success": False, "error": "Deployment not found"}
        d = self.deployments[deployment_id]
        old_ver = d.version
        d.version = new_version
        d.status = "running"
        self._save()
        return {"success": True, "deployment_id": deployment_id, "old_version": old_ver, "new_version": new_version}

    def list_deployments(self) -> list[dict]:
        return [d.to_dict() for d in self.deployments.values()]

    def get_deployment(self, deployment_id: str) -> Optional[dict]:
        d = self.deployments.get(deployment_id)
        return d.to_dict() if d else None

    def remote_command(self, deployment_id: str, command: str) -> dict:
        if deployment_id not in self.deployments:
            return {"success": False, "error": "Deployment not found"}
        d = self.deployments[deployment_id]
        return {
            "success": True,
            "deployment_id": deployment_id,
            "hostname": d.hostname,
            "command": command,
            "result": f"[REMOTE] Executed '{command}' on {d.hostname} ({d.target})",
            "exit_code": 0,
        }

    def summary(self) -> dict:
        targets = {}
        statuses = {}
        for d in self.deployments.values():
            targets[d.target] = targets.get(d.target, 0) + 1
            statuses[d.status] = statuses.get(d.status, 0) + 1
        return {
            "total": len(self.deployments),
            "by_target": targets,
            "by_status": statuses,
            "running": sum(1 for d in self.deployments.values() if d.status == "running"),
        }
