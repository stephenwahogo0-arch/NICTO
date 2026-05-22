"""Real deploy engine — deploys via SSH, Docker, or local subprocess."""
import json
import os
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Optional


class DeploymentTarget(str, Enum):
    LINUX_SERVER = "linux_server"
    RASPBERRY_PI = "raspberry_pi"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    ANDROID = "android"
    IOT = "iot"
    LOCAL = "local"


class DeploymentRecord:
    def __init__(self, target: DeploymentTarget, hostname: str, project_id: str):
        self.id = uuid.uuid4().hex[:12]
        self.target = target
        self.hostname = hostname
        self.project_id = project_id
        self.status = "pending"
        self.installed_at = None
        self.last_heartbeat = None
        self.created_at = time.time()
        self.error = None


class DeployEngine:
    def __init__(self, deploy_dir: Optional[str] = None):
        self.deploy_dir = Path(deploy_dir or os.path.join(str(Path.home()), ".nikto", "deployments"))
        self.deploy_dir.mkdir(parents=True, exist_ok=True)
        self.records = {}

    def deploy(self, target: DeploymentTarget, hostname: str, project_id: str, config: dict = None) -> dict:
        record = DeploymentRecord(target, hostname, project_id)
        self.records[record.id] = record
        try:
            success = self._do_deploy(record, config or {})
            if success:
                record.status = "running"
                record.installed_at = time.time()
                record.last_heartbeat = time.time()
            else:
                record.status = "failed"
            return {"success": success, "deployment_id": record.id, "target": target.value, "hostname": hostname, "status": record.status}
        except Exception as e:
            record.status = "failed"
            record.error = str(e)
            return {"success": False, "deployment_id": record.id, "error": str(e)}

    def _do_deploy(self, record: DeploymentRecord, config: dict) -> bool:
        if record.target == DeploymentTarget.LOCAL:
            deploy_path = self.deploy_dir / record.project_id
            deploy_path.mkdir(parents=True, exist_ok=True)
            (deploy_path / "deployed_at.txt").write_text(str(datetime.now()))
            return True
        elif record.target == DeploymentTarget.DOCKER:
            image = config.get("image", "python:3.11-slim")
            result = subprocess.run(["docker", "pull", image], capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                container_name = f"nikto_{record.project_id}"
                subprocess.run(["docker", "run", "-d", "--name", container_name, image, "sleep", "infinity"],
                               capture_output=True, timeout=30)
            return result.returncode == 0
        elif record.target in (DeploymentTarget.LINUX_SERVER, DeploymentTarget.RASPBERRY_PI):
            try:
                import paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=record.hostname, username=config.get("user", "root"),
                            key_filename=config.get("key_file"), timeout=15)
                sftp = ssh.open_sftp()
                remote_dir = f"/opt/nikto/{record.project_id}"
                sftp.mkdir(remote_dir)
                sftp.put(config.get("package_path", ""), f"{remote_dir}/nikto.tar.gz")
                ssh.exec_command(f"cd {remote_dir} && tar -xzf nikto.tar.gz && python3 install.py")
                ssh.close()
                return True
            except ImportError:
                return False
            except Exception as e:
                record.error = str(e)
                return False
        return False

    def remote_command(self, deployment_id: str, command: str) -> dict:
        record = self.records.get(deployment_id)
        if not record:
            return {"success": False, "error": "Deployment not found"}
        if record.target == DeploymentTarget.LOCAL:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {"success": result.returncode == 0, "command": command,
                    "result": result.stdout, "exit_code": result.returncode}
        elif record.target in (DeploymentTarget.LINUX_SERVER, DeploymentTarget.RASPBERRY_PI):
            try:
                import paramiko
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=record.hostname, username="root", timeout=15)
                _, stdout, stderr = ssh.exec_command(command, timeout=30)
                output = stdout.read().decode()
                error = stderr.read().decode()
                ssh.close()
                return {"success": True, "command": command, "result": output, "exit_code": 0}
            except Exception as e:
                return {"success": False, "command": command, "error": str(e), "exit_code": -1}
        return {"success": False, "command": command, "error": "Unsupported target", "exit_code": -1}

    def list_deployments(self) -> list:
        return [{"id": rid, "target": r.target.value, "hostname": r.hostname, "status": r.status} for rid, r in self.records.items()]
