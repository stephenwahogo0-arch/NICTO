import asyncio, json, time, uuid
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Optional

from nikto.config.settings import NiktoConfig
from nikto.memory.base import MemorySystem
from nikto.providers.base import create_provider
from nikto.tools.base import ToolResult, ToolRegistry


class AgentMode(str, Enum):
    PLAN = "plan"
    BUILD = "build"
    AUTONOMOUS = "autonomous"
    INTERACTIVE = "interactive"
    DAEMON = "daemon"


class AgentState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    TOOL_CALL = "tool_call"


class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


class AgentConfig:
    def __init__(self, model=None, mode: AgentMode = AgentMode.INTERACTIVE, system_prompt: str = "You are NIKTO, a modular AI agent."):
        self.model = model or NiktoConfig().model
        self.mode = mode
        self.system_prompt = system_prompt
        self.max_tokens = 4096
        self.temperature = 0.5


class Agent:
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.id = str(uuid.uuid4())[:12]
        self.state = AgentState.IDLE
        self.provider = create_provider(self.config.model)
        self.memory = MemorySystem()
        self.tool_registry = ToolRegistry()

    async def run(self, task: str, stream: bool = False) -> dict:
        self.state = AgentState.THINKING
        context = await self.memory.get_context(task)
        messages = [
            {"role": "system", "content": self.config.system_prompt},
            {"role": "user", "content": f"Context: {context}\n\nTask: {task}"},
        ]
        result = await self.provider.chat(messages, max_tokens=self.config.max_tokens, temperature=self.config.temperature)
        await self.memory.store(task, source="user")
        await self.memory.store(result.get("content", ""), source="nikto")
        self.state = AgentState.IDLE
        return result

    async def run_sync(self, prompt: str) -> str:
        result = await self.run(prompt)
        return result.get("content", "")

    def get_status(self) -> dict:
        info = self.provider.get_info()
        return {"id": self.id, "state": self.state.value, "mode": self.config.mode.value if hasattr(self.config.mode, 'value') else str(self.config.mode), "provider": info}
