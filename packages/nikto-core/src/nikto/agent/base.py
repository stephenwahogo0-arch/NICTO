import asyncio, json, time, uuid
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Optional, List

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
from nikto.language.detector import detector as lang_detector


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
    # Swarming configuration
    enable_swarming: bool = False
    max_swarm_depth: int = 2
    swarm_size: int = 2


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
        self._target_language = getattr(self.config.model, "language", None) or "auto"
        self._detected_language = None

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

        # Add language instruction
        if self._target_language and self._target_language != "auto":
            lang_name = lang_detector.name(self._target_language)
            base += f"\n## Language\nRespond in {lang_name} ({self._target_language}).\n"

        brain_context = self.brain.get_context_string()
        if brain_context:
            base += f"\n\n{brain_context}"

        return base

    async def run(
        self, task: str, stream: Optional[bool] = None
    ) -> AsyncGenerator[dict, None]:
        # Check if swarming is enabled and task is complex enough to warrant swarming
        if (self.agent_config.enable_swarming and 
            self._should_swarm(task) and 
            self.turn_count < self.agent_config.max_swarm_depth):
            async for result in self._run_swarm(task, stream):
                yield result
            return
            
        self._running = True
        self.state = AgentState.THINKING
        self.turn_count = 0

        # Auto-detect language from user input
        if self._target_language == "auto":
            detected = lang_detector.detect(task)
            self._detected_language = detected
        else:
            self._detected_language = self._target_language

        brain_result = self.brain.think(task, {"turn": self.turn_count, "session_id": self.session_id})
        self._emit("brain", {"result": brain_result})

        system_prompt = self._build_system_prompt()
        # Inject detected language instruction into system prompt
        if self._target_language == "auto":
            lang_name = lang_detector.name(self._detected_language)
            system_prompt += f"\n\n## Language Instruction\nDetected user language: {lang_name} ({self._detected_language}). Always respond in the same language as the user.\n"

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

    def _should_swarm(self, task: str) -> bool:
        """Determine if a task is complex enough to warrant swarming."""
        # Simple heuristic: longer tasks or tasks with multiple sentences are more complex
        word_count = len(task.split())
        sentence_count = len([s for s in task.split('.') if s.strip()])
        
        # Swarm if task is longer than 20 words or has multiple sentences
        return word_count > 20 or sentence_count > 2

    async def _run_swarm(self, task: str, stream: Optional[bool] = None) -> AsyncGenerator[dict, None]:
        """Run a task using a swarm of sub-agents."""
        yield {
            "type": "swarm_start",
            "content": f"Starting swarm with {self.agent_config.swarm_size} agents for complex task..."
        }
        
        # Decompose the task into subtasks
        subtasks = self._decompose_task(task, self.agent_config.swarm_size)
        
        # Create sub-agents
        sub_agents = []
        for i, subtask in enumerate(subtasks):
            sub_agent_config = AgentConfig(
                enable_swarming=self.agent_config.enable_swarming,
                max_swarm_depth=max(0, self.agent_config.max_swarm_depth - 1),
                swarm_size=self.agent_config.swarm_size,
                stream=self.agent_config.stream,
                thinking=self.agent_config.thinking
            )
            
            sub_agent = Agent(
                config=self.config,
                agent_config=sub_agent_config,
                tool_registry=self.tool_registry,
                memory=self.memory,
                skill_runtime=self.skill_runtime,
                variant=self.variant
            )
            sub_agents.append((sub_agent, subtask))
        
        # Run all sub-agents concurrently and collect results
        results = []
        for i, (sub_agent, subtask) in enumerate(sub_agents):
            async for chunk in sub_agent.run(subtask, stream):
                # Relay chunks from sub-agents with metadata
                yield {
                    "type": "swarm_chunk",
                    "agent_index": i,
                    "subtask": subtask[:100] + "..." if len(subtask) > 100 else subtask,
                    "chunk": chunk
                }
                
                if chunk.get("type") == "done":
                    results.append({
                        "agent_index": i,
                        "subtask": subtask,
                        "result": chunk.get("content", "")
                    })
        
        # Synthesize results from all sub-agents
        yield {
            "type": "swarm_synthesizing",
            "content": f"Synthesizing results from {len(results)} sub-agents..."
        }
        
        # Simple synthesis: concatenate results
        synthesized_result = self._synthesize_results(results, task)
        
        yield {
            "type": "swarm_complete",
            "content": synthesized_result
        }

    def _decompose_task(self, task: str, num_agents: int) -> List[str]:
        """Decompose a complex task into subtasks for swarming."""
        # Simple decomposition: split by sentences or create equal parts
        sentences = [s.strip() for s in task.split('.') if s.strip()]
        
        if len(sentences) >= num_agents:
            # Distribute sentences among agents
            subtasks = []
            sentences_per_agent = max(1, len(sentences) // num_agents)
            
            for i in range(num_agents):
                start_idx = i * sentences_per_agent
                end_idx = start_idx + sentences_per_agent if i < num_agents - 1 else len(sentences)
                subtask = '. '.join(sentences[start_idx:end_idx]) + ('.' if end_idx < len(sentences) else '')
                subtasks.append(subtask)
                
            return subtasks
        else:
            # Fallback: create similar tasks with different focuses
            base_task = task.strip()
            subtasks = []
            for i in range(num_agents):
                subtasks.append(f"{base_task} (focus area {i+1} of {num_agents})")
            return subtasks

    def _synthesize_results(self, results: List[dict], original_task: str) -> str:
        """Synthesize results from multiple sub-agents into a coherent response."""
        if not results:
            return "No results generated from swarm."
        
        if len(results) == 1:
            return results[0]["result"]
        
        # Simple synthesis: combine results with clear attribution
        synthesis = f"Swarm Results for: {original_task}\n\n"
        
        for result in results:
            synthesis += f"Sub-agent {result['agent_index'] + 1}:\n"
            synthesis += f"Task: {result['subtask']}\n"
            synthesis += f"Result: {result['result']}\n\n"
        
        synthesis += "\n--- Synthesis Complete ---\n"
        synthesis += "All sub-agents have completed their tasks. Results above show individual contributions."
        
        return synthesis

    async def run_sync(self, task: str) -> str:
        result = ""
        async for chunk in self.run(task, stream=False):
            if chunk.get("type") == "done":
                result = chunk.get("content", "")
        return result

    def stop(self):
        self._running = False
        self.state = AgentState.DONE
