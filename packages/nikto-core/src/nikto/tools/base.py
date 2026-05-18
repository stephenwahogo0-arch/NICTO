import json
from typing import Any, Callable, Optional

from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool = True
    output: str = ""
    error: Optional[str] = None
    data: Any = None


class Tool(BaseModel):
    name: str
    description: str
    parameters: dict
    function: Optional[Callable] = None
    async_function: Optional[Callable] = None

    def to_openai_format(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def register_many(self, tools: list[Tool]):
        for t in tools:
            self.register(t)

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def get_openai_tools(self) -> list[dict]:
        return [t.to_openai_format() for t in self._tools.values()]

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    async def execute(self, name: str, **kwargs) -> Any:
        tool = self._tools.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found. Available: {', '.join(self.list_tools())}"

        try:
            if tool.async_function:
                result = await tool.async_function(**kwargs)
            elif tool.function:
                result = tool.function(**kwargs)
            else:
                return "Error: No function registered for this tool."

            if isinstance(result, ToolResult):
                if result.error:
                    return f"Error: {result.error}"
                return result.output or result.data
            return str(result) if result is not None else "Done."

        except Exception as e:
            return f"Error executing {name}: {str(e)}"
