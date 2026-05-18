import asyncio
import os
import subprocess
import sys
from pathlib import Path

from nikto.tools.base import Tool


async def tool_bash(command: str, workdir: Optional[str] = None, timeout: int = 120) -> str:
    shell = os.environ.get("SHELL", "powershell" if sys.platform == "win32" else "bash")

    try:
        if workdir:
            workdir = str(Path(workdir).expanduser().resolve())
            os.makedirs(workdir, exist_ok=True)

        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workdir,
            shell=True,
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return f"Error: Command timed out after {timeout}s"

        output = ""
        if stdout:
            output += stdout.decode("utf-8", errors="replace")
        if stderr:
            stderr_text = stderr.decode("utf-8", errors="replace")
            if stderr_text:
                output += f"\n[STDERR]\n{stderr_text}"

        if not output:
            output = f"Command completed with exit code {proc.returncode}"

        if len(output) > 100000:
            output = output[:100000] + "\n... (truncated at 100K chars)"

        return output

    except Exception as e:
        return f"Error executing command: {str(e)}"


BashTool = Tool(
    name="bash",
    description="Execute a bash/shell command. Use for running scripts, building, testing, etc.",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to execute"},
            "workdir": {"type": "string", "description": "Working directory for the command"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 120)"},
        },
        "required": ["command"],
    },
    async_function=tool_bash,
)
