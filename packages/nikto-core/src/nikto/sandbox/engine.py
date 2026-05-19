import enum
import json
import random
import string
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


class SandboxType(enum.Enum):
    DOCKER = "docker"
    VM = "vm"
    NETWORK = "network"
    CODE = "code"
    FULL_OS = "full_os"
    CONTAINER = "container"
    CLOUD = "cloud"
    CHROOT = "chroot"
    FIREJAIL = "firejail"
    KUBERNETES = "kubernetes"


@dataclass
class SandboxInstance:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    stype: SandboxType = SandboxType.DOCKER
    status: str = "creating"
    spec: dict = field(default_factory=dict)
    isolation_level: str = "full"
    network_access: bool = False
    persistent: bool = False
    created_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "stype": self.stype.value, "status": self.status,
            "spec": self.spec, "isolation_level": self.isolation_level,
            "network_access": self.network_access, "persistent": self.persistent,
            "created_at": self.created_at, "metadata": self.metadata,
        }


SANDBOX_TEMPLATES = {
    "docker": {
        "description": "Docker container sandbox — full filesystem isolation, resource limits, network control",
        "specs": ["cpu_limit", "memory_limit", "read_only_fs", "network_disabled", "seccomp_profile"],
        "default_spec": {"cpu_limit": "2", "memory_limit": "2g", "read_only_fs": True, "network_disabled": False, "seccomp_profile": "default"},
    },
    "vm": {
        "description": "Full virtual machine sandbox — hardware-level isolation, arbitrary OS, snapshot/restore",
        "specs": ["vcpus", "ram_mb", "disk_gb", "os_image", "nested_virt", "snapshot_support"],
        "default_spec": {"vcpus": 2, "ram_mb": 4096, "disk_gb": 20, "os_image": "ubuntu-22.04", "nested_virt": False, "snapshot_support": True},
    },
    "code": {
        "description": "Code execution sandbox — jailed runtime, whitelisted syscalls, timeout enforcement",
        "specs": ["language", "timeout_sec", "max_memory_mb", "allowed_modules", "max_filesize_kb"],
        "default_spec": {"language": "python", "timeout_sec": 30, "max_memory_mb": 256, "allowed_modules": ["json", "math", "random"], "max_filesize_kb": 100},
    },
    "network": {
        "description": "Network sandbox — isolated virtual network, traffic capture, MITM simulation",
        "specs": ["subnet", "dns_domain", "num_hosts", "capture_traffic", "firewall_rules"],
        "default_spec": {"subnet": "10.0.0.0/24", "dns_domain": "sandbox.local", "num_hosts": 5, "capture_traffic": True, "firewall_rules": "deny_all"},
    },
    "full_os": {
        "description": "Full OS sandbox — complete operating system environment with all services",
        "specs": ["os_type", "desktop_env", "services", "users", "network_profile"],
        "default_spec": {"os_type": "linux", "desktop_env": "xfce", "services": ["ssh", "nginx"], "users": ["nikto"], "network_profile": "isolated"},
    },
}


class SandboxEngine:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or "~/.nikto").expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.data_dir / "sandboxes.json"
        self.sandboxes: dict[str, SandboxInstance] = {}
        self._load()

    def _load(self):
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text())
                for sid, sdata in data.items():
                    sdata["stype"] = SandboxType(sdata["stype"])
                    self.sandboxes[sid] = SandboxInstance(**sdata)
            except Exception:
                pass

    def _save(self):
        data = {sid: s.to_dict() for sid, s in self.sandboxes.items()}
        self.store_path.write_text(json.dumps(data, indent=2))

    def create_sandbox(self, stype: str, name: str = "", spec: Optional[dict] = None) -> dict:
        try:
            stype_enum = SandboxType(stype)
        except ValueError:
            return {"success": False, "error": f"Invalid type: {stype}. Valid: {[t.value for t in SandboxType]}"}

        template = SANDBOX_TEMPLATES.get(stype, {})
        default_spec = template.get("default_spec", {})
        merged_spec = {**default_spec, **(spec or {})}

        instance = SandboxInstance(
            name=name or f"{stype}-sandbox-{random.randint(1000,9999)}",
            stype=stype_enum,
            status="creating",
            spec=merged_spec,
            isolation_level=merged_spec.get("isolation_level", "full"),
            network_access=merged_spec.get("network_access", False),
        )
        instance.status = "running"
        self.sandboxes[instance.id] = instance
        self._save()
        return {"success": True, "instance": instance.to_dict(), "template": template.get("description", "")}

    def destroy_sandbox(self, sandbox_id: str) -> dict:
        if sandbox_id not in self.sandboxes:
            return {"success": False, "error": "Sandbox not found"}
        self.sandboxes[sandbox_id].status = "destroyed"
        self._save()
        return {"success": True, "sandbox_id": sandbox_id}

    def list_sandboxes(self) -> list[dict]:
        return [s.to_dict() for s in self.sandboxes.values()]

    def get_sandbox(self, sandbox_id: str) -> Optional[dict]:
        s = self.sandboxes.get(sandbox_id)
        return s.to_dict() if s else None

    def execute_in_sandbox(self, sandbox_id: str, command: str) -> dict:
        if sandbox_id not in self.sandboxes:
            return {"success": False, "error": "Sandbox not found"}
        s = self.sandboxes[sandbox_id]
        if s.status != "running":
            return {"success": False, "error": f"Sandbox status is {s.status}, not running"}
        execution_id = str(uuid.uuid4())[:8]
        result = {
            "execution_id": execution_id,
            "sandbox_id": sandbox_id,
            "command": command[:500],
            "exit_code": 0,
            "stdout": f"[SIMULATED] Command '{command}' executed in {s.name} ({s.stype.value}) sandbox",
            "stderr": "",
            "execution_time_ms": random.randint(1, 5000),
        }
        s.metadata.setdefault("executions", []).append(result)
        self._save()
        return {"success": True, "result": result}

    def snapshot_sandbox(self, sandbox_id: str) -> dict:
        if sandbox_id not in self.sandboxes:
            return {"success": False, "error": "Sandbox not found"}
        s = self.sandboxes[sandbox_id]
        snap_id = str(uuid.uuid4())[:8]
        snap = {"id": snap_id, "timestamp": time.time(), "state": s.to_dict()}
        s.metadata.setdefault("snapshots", []).append(snap)
        self._save()
        return {"success": True, "snapshot": snap}

    def summary(self) -> dict:
        types = {}
        statuses = {}
        for s in self.sandboxes.values():
            t = s.stype.value
            types[t] = types.get(t, 0) + 1
            st = s.status
            statuses[st] = statuses.get(st, 0) + 1
        return {
            "total": len(self.sandboxes),
            "by_type": types,
            "by_status": statuses,
            "running": sum(1 for s in self.sandboxes.values() if s.status == "running"),
        }
