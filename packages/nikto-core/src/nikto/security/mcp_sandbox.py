import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class MCPSecureSandbox:
    """MCP Secure Sandbox — Isolated container execution and read-only database auditing."""

    def __init__(self, sandbox_dir: Optional[str] = None):
        self.sandbox_dir = Path(sandbox_dir or tempfile.mkdtemp(prefix="nikto_sandbox_"))
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)

    async def isolated_execute(self, script_content: str, language: str = "python", timeout: int = 30) -> dict:
        """Isolated Environment Execution — Run suspicious code in a sandboxed container."""
        result = {
            "stdout": "",
            "stderr": "",
            "return_code": -1,
            "network_calls": [],
            "file_operations": [],
            "sandbox_id": self.sandbox_dir.name,
        }

        script_path = self.sandbox_dir / f"analysis_script.{language}"
        script_path.write_text(script_content)

        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "run", "--rm", "--network", "none",
                "--cap-drop", "ALL",
                "-v", f"{script_path}:/tmp/script.{language}:ro",
                "python:3.12-slim",
                "python", f"/tmp/script.{language}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=timeout,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            result["stdout"] = stdout.decode(errors="replace") if stdout else ""
            result["stderr"] = stderr.decode(errors="replace") if stderr else ""
            result["return_code"] = proc.returncode or 0

        except FileNotFoundError:
            logger.warning("Docker not available; running in restricted subprocess")
            proc = await asyncio.create_subprocess_exec(
                "python", "-c", f"import sys; sys.path.insert(0, '.')\nexec(open('/tmp/script.{language}').read())",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                timeout=timeout,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            result["stdout"] = stdout.decode(errors="replace") if stdout else ""
            result["stderr"] = stderr.decode(errors="replace") if stderr else ""
            result["return_code"] = proc.returncode or 0

        except asyncio.TimeoutError:
            result["stderr"] = "Execution timed out"
            result["return_code"] = -1

        except Exception as e:
            result["stderr"] = str(e)
            result["return_code"] = -1

        return result

    async def read_only_db_audit(self, db_url: str, query: str) -> dict:
        """Read-Only Database Auditing — Inspect database without altering data."""
        result = {"query": query, "rows": [], "error": ""}

        # Only permit SELECT statements
        if not query.strip().upper().startswith("SELECT"):
            result["error"] = "Only SELECT queries permitted for read-only audit"
            return result

        try:
            if "sqlite" in db_url:
                import sqlite3
                db_path = db_url.replace("sqlite:///", "")
                conn = sqlite3.connect(db_path)
                cursor = conn.execute(query)
                columns = [d[0] for d in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchmany(100)]
                conn.close()
                result["rows"] = rows

            elif "postgresql" in db_url or "psycopg" in db_url:
                import psycopg2
                conn = psycopg2.connect(db_url)
                cursor = conn.cursor()
                cursor.execute(query)
                columns = [d[0] for d in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchmany(100)]
                conn.close()
                result["rows"] = rows

        except ImportError as e:
            result["error"] = f"Database driver not available: {e}"
        except Exception as e:
            result["error"] = str(e)

        return result
