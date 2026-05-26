from typing import Optional, Callable, Any
from uuid import uuid4


class ToolResult:
    def __init__(self, success: bool = True, output: str = "", error: str = "", data: dict = None):
        self.success = success
        self.output = output
        self.error = error
        self.data = data or {}


class Tool:
    name: str = ""
    description: str = ""

    def __init__(self):
        self.id = str(uuid4())[:12]

    async def execute(self, **kwargs) -> dict:
        raise NotImplementedError


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._func_tools: dict[str, Callable] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def register_many(self, *tools: Tool):
        for t in tools:
            self.register(t)

    def register_func(self, name: str, func: Callable, description: str = ""):
        self._func_tools[name] = func

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def get_func(self, name: str) -> Optional[Callable]:
        return self._func_tools.get(name)

    def list_tools(self) -> list[dict]:
        result = []
        for name, tool in self._tools.items():
            result.append({"name": name, "description": tool.description, "type": "class"})
        for name, func in self._func_tools.items():
            result.append({"name": name, "description": getattr(func, "__doc__", "") or "", "type": "function"})
        return result

    async def execute(self, name: str, **kwargs) -> dict:
        tool = self._tools.get(name)
        if tool:
            return await tool.execute(**kwargs)
        func = self._func_tools.get(name)
        if func:
            result = func(**kwargs)
            if hasattr(result, "__await__"):
                result = await result
            return {"success": True, "result": result}
        return {"success": False, "error": f"Tool '{name}' not found"}
