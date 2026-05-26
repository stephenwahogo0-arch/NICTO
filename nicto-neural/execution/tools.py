"""Tool registry — available tools for NICTO to use."""

import subprocess
from pathlib import Path


class ToolRegistry:
    """Registry of tools available to NICTO for task execution."""

    def __init__(self):
        self._tools: dict[str, dict] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        self.register("file_read", self._file_read, "Read a file from disk")
        self.register("file_write", self._file_write, "Write content to a file")
        self.register("shell_exec", self._shell_exec, "Execute a shell command")
        self.register("web_search", self._web_search, "Search the web")

    def register(self, name: str, func, description: str = "") -> None:
        self._tools[name] = {"func": func, "description": description}

    def execute(self, tool_name: str, **kwargs) -> dict:
        if tool_name not in self._tools:
            return {"error": f"Unknown tool: {tool_name}", "success": False}
        try:
            result = self._tools[tool_name]["func"](**kwargs)
            return {"result": result, "success": True, "tool": tool_name}
        except Exception as e:
            return {"error": str(e), "success": False, "tool": tool_name}

    def list_tools(self) -> list[dict]:
        return [
            {"name": k, "description": v["description"]}
            for k, v in self._tools.items()
        ]

    def _file_read(self, path: str) -> str:
        return Path(path).read_text()

    def _file_write(self, path: str, content: str) -> str:
        Path(path).write_text(content)
        return f"Written {len(content)} bytes to {path}"

    def _shell_exec(self, command: str, timeout: int = 30) -> str:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout or result.stderr

    def _web_search(self, query: str) -> str:
        return f"[Web search for: {query}] — requires external API integration"
