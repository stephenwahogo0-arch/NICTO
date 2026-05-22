import asyncio, json, time, uuid
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Optional

from pydantic import BaseModel, Field

from nikto.config.settings import NiktoConfig
from nikto.memory.base import MemorySystem
from nikto.providers.base import create_provider
from nikto.skills.base import SkillRuntime
from nikto.tools.base import ToolResult, ToolRegistry
from nikto.brain.engine import BrainEngine
from nikto.games.engine import GameEngine
from nikto.sourcing.engine import SourcingEngine
from nikto.voice.engine import VoiceEngine, VoiceProfile
from nikto.evolution.protocol import EvolutionProtocol
from nikto.infinite_context import InfiniteContextEngine
from nikto.training.hourly import HourlyTrainer


class AgentMode(str, Enum):
    PLAN = "plan"
    BUILD = "build"


class AgentState(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    RESPONDING = "responding"
    ERROR = "error"
    DONE = "done"


class Message(BaseModel):
    role: str
    content: str
    tool_calls: Optional[list[dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class AgentConfig(BaseModel):
    mode: AgentMode = AgentMode.BUILD
    max_turns: int = 25
    max_tool_calls_per_turn: int = 10
    system_prompt: Optional[str] = None
    stream: bool = True
    thinking: bool = False


class Agent:
    def __init__(
        self,
        config: NiktoConfig,
        agent_config: Optional[AgentConfig] = None,
        tool_registry: Optional[ToolRegistry] = None,
        memory: Optional[MemorySystem] = None,
        skill_runtime: Optional[SkillRuntime] = None,
        variant: Optional["AgentVariant"] = None,
    ):
        self.variant = variant
        self.config = config or NiktoConfig.load()
        self.agent_config = agent_config or AgentConfig()
        if self.config.mode == "plan":
            self.agent_config.mode = AgentMode.PLAN

        self.tool_registry = tool_registry or ToolRegistry()
        self.memory = memory or MemorySystem(self.config.memory)
        self.skill_runtime = skill_runtime or SkillRuntime()
        self.brain = BrainEngine(data_dir=self.config.data_dir)
        self.games = GameEngine()
        self.sourcing = SourcingEngine(data_dir=self.config.data_dir)
        self.voice = VoiceEngine(data_dir=self.config.data_dir)
        self.evolution = EvolutionProtocol(data_dir=self.config.data_dir)
        self.infinite_context = InfiniteContextEngine()

        self.provider = create_provider(self.config.model)
        self.session_id = uuid.uuid4().hex[:12]
        self.messages: list[Message] = []
        self.state = AgentState.IDLE
        self.turn_count = 0
        self._callbacks: list[Callable] = []
        self._running = False
        self._learning_log = []
        self.trainer = HourlyTrainer(data_dir=self.config.data_dir)
        self.trainer.start_auto_train(interval_hours=1)

    def on_event(self, callback: Callable):
        self._callbacks.append(callback)

    def _emit(self, event: str, data: Any):
        for cb in self._callbacks:
            try:
                cb(event, data)
            except Exception:
                pass

    def _build_system_prompt(self) -> str:
        if self.variant:
            return self.variant.build_system_prompt()

        base = "You are NIKTO, a capable local AI system.\n\n"
        base += "CAPABILITIES:\n"
        base += "- Chat and answer questions\n"
        base += "- Read, write, edit files\n"
        base += "- Execute bash commands\n"
        base += "- Search the web for information\n"
        base += "- Generate images from descriptions\n"
        base += "- Speak via text-to-speech\n"
        base += "- Play games (Pong, Snake, Tetris, Platformer, RPG)\n"
        base += "- Remember past conversations\n"
        base += "- Learn from interactions\n\n"
        base += "Be helpful, direct, and honest. Use tools when needed.\n"

        if self.agent_config.system_prompt:
            base += f"\n## Additional Instructions\n{self.agent_config.system_prompt}\n"

        brain_context = self.brain.get_context_string()
        if brain_context:
            base += f"\n\n{brain_context}"

        return base

    async def run(
        self, task: str, stream: Optional[bool] = None
    ) -> AsyncGenerator[dict, None]:
        self._running = True
        self.state = AgentState.THINKING
        self.turn_count = 0

        brain_result = self.brain.think(task, {"turn": self.turn_count, "session_id": self.session_id})
        self._emit("brain", {"result": brain_result})

        system_prompt = self._build_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]

        context = await self.memory.get_context(task)
        if context:
            messages.append({"role": "system", "content": f"## Memory Context\n{context}"})

        messages.append({"role": "user", "content": task})
        self.evolution.record_learning(task, "processing", complexity=2)
        should_stream = stream if stream is not None else self.agent_config.stream

        while self._running and self.turn_count < self.agent_config.max_turns:
            self.state = AgentState.THINKING
            self._emit("thinking", {"turn": self.turn_count})

            tools_dict = self.tool_registry.get_openai_tools()

            if should_stream:
                collected_message = ""
                collected_tool_calls = []
                async for chunk in self.provider.stream_chat(
                    messages=messages,
                    tools=tools_dict if tools_dict else None,
                    temperature=self.config.model.temperature,
                    max_tokens=self.config.model.max_tokens,
                ):
                    yield chunk
                    if "content" in chunk and chunk["content"]:
                        collected_message += chunk["content"] or ""
                    if "tool_calls" in chunk:
                        for tc in chunk["tool_calls"]:
                            collected_tool_calls.append(tc)
                final_content = collected_message
                tool_calls = collected_tool_calls
            else:
                response = await self.provider.chat(
                    messages=messages,
                    tools=tools_dict if tools_dict else None,
                    temperature=self.config.model.temperature,
                    max_tokens=self.config.model.max_tokens,
                )
                final_content = response.get("content", "")
                tool_calls = response.get("tool_calls", [])
                yield {"type": "response", "content": final_content}

            self.messages.append(Message(role="assistant", content=final_content, tool_calls=tool_calls))

            if not tool_calls:
                self.state = AgentState.DONE
                self._emit("done", {"content": final_content})
                await self.memory.store(task, final_content)
                self.brain.store_memory(f"task_{self.session_id}_{self.turn_count}", final_content[:500])
                self._learning_log.append({"input": task, "output": final_content[:200], "time": time.time()})
                sourcing_summary = self.sourcing.get_session_summary()
                yield {"type": "done", "content": final_content, "sources": sourcing_summary}
                break

            self.state = AgentState.TOOL_CALL
            self._emit("tool_calls", {"calls": tool_calls})

            for tc in tool_calls:
                func_name = tc.get("function", {}).get("name", "")
                func_args_str = tc.get("function", {}).get("arguments", "{}")
                tool_call_id = tc.get("id", uuid.uuid4().hex[:12])
                try:
                    func_args = json.loads(func_args_str)
                except json.JSONDecodeError:
                    func_args = {}
                self._emit("tool_call", {"name": func_name, "args": func_args})
                result = await self.tool_registry.execute(func_name, **func_args)
                result_str = str(result) if result is not None else "Tool completed successfully."
                if len(result_str) > 50000:
                    result_str = result_str[:50000] + "\n... (truncated)"
                messages.append({
                    "role": "assistant", "content": None,
                    "tool_calls": [{"id": tool_call_id, "type": "function",
                                    "function": {"name": func_name, "arguments": func_args_str}}],
                })
                messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": result_str})
                yield {"type": "tool_result", "name": func_name, "result": result_str[:500]}
                await self.memory.store_tool_call(func_name, func_args, result_str[:1000])

            self.turn_count += 1

        self._running = False
        if self.turn_count >= self.agent_config.max_turns:
            yield {"type": "limit_reached", "message": "Max turns reached"}

    async def run_sync(self, task: str) -> str:
        result = ""
        async for chunk in self.run(task, stream=False):
            if chunk.get("type") == "done":
                result = chunk.get("content", "")
        return result

    def stop(self):
        self._running = False
        self.state = AgentState.DONE
