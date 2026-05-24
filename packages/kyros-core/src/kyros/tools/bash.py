import asyncio
import subprocess
import shlex
from kyros.tools.base import Tool


class BashTool(Tool):
    name = "bash"
    description = "Execute a shell command"

    async def execute(self, command: str, timeout: int = 120, workdir: str = None, **kwargs) -> dict:
        try:
            cwd = workdir or None
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "success": proc.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "exit_code": proc.returncode,
                "command": command,
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": f"Command timed out after {timeout}s", "command": command}
        except Exception as e:
            return {"success": False, "error": str(e), "command": command}
