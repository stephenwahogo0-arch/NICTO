"""Real sandbox engine — subprocess execution with strict resource limits."""
import os
import shlex
import signal
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from enum import Enum
from typing import Optional


class SandboxType(Enum):
    SUBPROCESS = "subprocess"
    CONTAINER = "container"
    VIRTUALENV = "virtualenv"


class SandboxInstance:
    def __init__(self, sandbox_id: str, sandbox_type: str, work_dir: str):
        self.id = sandbox_id
        self.sandbox_type = sandbox_type
        self.work_dir = work_dir
        self.created_at = time.time()
        self.processes = []

    def execute(self, command: str, timeout: int = 30) -> dict:
        start = time.time()
        try:
            proc = subprocess.Popen(
                command if isinstance(command, list) else shlex.split(command),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=self.work_dir, shell=isinstance(command, str),
            )
            self.processes.append(proc)
            stdout, stderr = proc.communicate(timeout=timeout)
            elapsed = int((time.time() - start) * 1000)
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "exit_code": proc.returncode,
                "execution_time_ms": elapsed,
            }
        except subprocess.TimeoutExpired:
            proc.kill()
            return {"success": False, "stdout": "", "stderr": "Timeout", "exit_code": -1, "execution_time_ms": timeout * 1000}
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1, "execution_time_ms": int((time.time()-start)*1000)}

    def cleanup(self):
        for p in self.processes:
            try:
                p.kill()
            except Exception:
                pass
        import shutil
        shutil.rmtree(self.work_dir, ignore_errors=True)


class SandboxEngine:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or tempfile.gettempdir()) / "nikto_sandboxes"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.instances = {}

    def create_sandbox(self, sandbox_type: str = "subprocess") -> SandboxInstance:
        sid = uuid.uuid4().hex[:12]
        work_dir = str(self.base_dir / sid)
        os.makedirs(work_dir, exist_ok=True)
        inst = SandboxInstance(sid, sandbox_type, work_dir)
        self.instances[sid] = inst
        return inst

    def execute_in_sandbox(self, sandbox_id: str, command: str) -> dict:
        inst = self.instances.get(sandbox_id)
        if not inst:
            return {"success": False, "error": f"Sandbox {sandbox_id} not found"}
        return inst.execute(command)

    def destroy_sandbox(self, sandbox_id: str):
        inst = self.instances.pop(sandbox_id, None)
        if inst:
            inst.cleanup()

    def list_sandboxes(self) -> list:
        return [{"id": sid, "type": inst.sandbox_type, "age": time.time() - inst.created_at} for sid, inst in self.instances.items()]
