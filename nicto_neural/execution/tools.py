import subprocess
import sys
from typing import Any, Callable, Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class ToolSpec:
    name: str
    func: Callable
    description: str
    parameters: Dict[str, str] = field(default_factory=dict)


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register("search_knowledge", self._search_knowledge, "Search knowledge base for information", {"query": "str"})
        self.register("execute_code", self._execute_code, "Execute Python code snippet", {"code": "str"})
        self.register("query_memory", self._query_memory, "Query memory store", {"query": "str", "limit": "int"})
        self.register("call_llm", self._call_llm, "Call external LLM", {"prompt": "str"})

    def register(self, name: str, func: Callable, description: str, parameters: Dict[str, str] = None):
        self._tools[name] = ToolSpec(name=name, func=func, description=description, parameters=parameters or {})

    def call(self, name: str, **kwargs) -> Any:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found. Available: {list(self._tools.keys())}")
        return self._tools[name].func(**kwargs)

    def list_tools(self) -> List[Dict]:
        return [{"name": t.name, "description": t.description, "parameters": t.parameters} for t in self._tools.values()]

    def get_tool(self, name: str) -> Tuple[Callable, str]:
        t = self._tools.get(name)
        if t is None:
            return None, ""
        return t.func, t.description

    def _search_knowledge(self, query: str) -> str:
        return f"Searched knowledge base for: {query}"

    def _execute_code(self, code: str) -> str:
        try:
            result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
            return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Code execution timed out"

    def _query_memory(self, query: str, limit: int = 10) -> str:
        return f"Queried memory for '{query}' (limit={limit})"

    def _call_llm(self, prompt: str) -> str:
        return f"LLM response to: {prompt[:50]}..."
