import asyncio, json, re, time, uuid, tempfile
from enum import Enum
from pathlib import Path
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

    # ── Intelligence Expansion: build_app, detect_language, translate_code ──

    async def build_app(self, description: str) -> dict:
        """Build a complete app scaffold from a plain English description.

        Detects the app type, selects the best language/framework, and generates
        a full project with working boilerplate, README, Dockerfile, tests, and
        environment config.
        """
        desc_lower = description.lower()

        # Detect app type and select technology
        if any(w in desc_lower for w in ("rest api", "api server", "backend api", "crud")):
            app_type = "rest_api"
            if any(w in desc_lower for w in ("go", "golang")):
                language, framework = "go", "gin"
            elif any(w in desc_lower for w in ("rust",)):
                language, framework = "rust", "axum"
            elif any(w in desc_lower for w in ("java", "spring")):
                language, framework = "java", "spring-boot"
            elif any(w in desc_lower for w in ("c#", "csharp", ".net", "dotnet")):
                language, framework = "csharp", ".net"
            elif any(w in desc_lower for w in ("node", "express", "javascript", "typescript")):
                language, framework = "node", "express"
            else:
                language, framework = "python", "fastapi"
            reason = f"{framework} chosen: " + {
                "fastapi": "async-first, auto-generated OpenAPI docs, Pydantic validation, fastest Python framework",
                "gin": "Go gives excellent concurrency and low latency for high-throughput APIs",
                "axum": "Rust provides memory safety with zero-cost abstractions and maximum performance",
                "spring-boot": "enterprise-grade with built-in DI, JPA, security, and massive ecosystem",
                ".net": "strong typing, excellent tooling, and high performance with ASP.NET Core",
                "express": "huge ecosystem, fast prototyping, and universal JavaScript/TypeScript support",
            }.get(framework, "best fit for the described requirements")
        elif any(w in desc_lower for w in ("mobile app", "ios", "android", "phone")):
            app_type = "mobile"
            if any(w in desc_lower for w in ("ios only", "swift", "iphone")):
                language, framework = "swift", "swiftui"
            elif any(w in desc_lower for w in ("android only", "kotlin")):
                language, framework = "kotlin", "compose"
            elif any(w in desc_lower for w in ("react native", "rn")):
                language, framework = "javascript", "react-native"
            else:
                language, framework = "dart", "flutter"
            reason = f"{framework} chosen: " + {
                "flutter": "single codebase for iOS + Android + Web, Riverpod for state, Material3 out of the box",
                "swiftui": "native iOS performance, first-party Apple support, Combine for reactive data",
                "compose": "modern declarative Android UI, Kotlin coroutines, Material3 integration",
                "react-native": "leverage existing React/JS skills, large community, Expo for rapid development",
            }.get(framework, "best fit for mobile requirements")
        elif any(w in desc_lower for w in ("cli", "command line", "terminal tool")):
            app_type = "cli"
            if any(w in desc_lower for w in ("go", "golang")):
                language, framework = "go", "cobra"
            elif any(w in desc_lower for w in ("rust",)):
                language, framework = "rust", "clap"
            else:
                language, framework = "python", "click"
            reason = f"{framework} chosen: " + {
                "click": "Python CLI standard, composable commands, type validation, auto-help generation",
                "cobra": "Go compiles to single binary, ideal for distributing CLI tools without runtime deps",
                "clap": "Rust gives native performance with derive macros for zero-boilerplate CLI parsing",
            }.get(framework, "optimal for CLI development")
        elif any(w in desc_lower for w in ("discord bot", "telegram bot", "chat bot")):
            app_type = "bot"
            platform = "telegram" if "telegram" in desc_lower else "discord"
            language, framework = "python", f"{platform}-bot"
            reason = f"Python has the most mature {platform} bot libraries with async support"
        elif any(w in desc_lower for w in ("smart contract", "blockchain", "token", "nft", "erc")):
            app_type = "smart_contract"
            language, framework = "solidity", "hardhat"
            reason = "Solidity is the EVM standard; Hardhat provides testing, deployment, and debugging"
        elif any(w in desc_lower for w in ("game", "2d game", "love2d")):
            app_type = "game"
            language, framework = "lua", "love2d"
            reason = "Love2D is lightweight, beginner-friendly, and perfect for 2D game prototyping"
        elif any(w in desc_lower for w in ("graphql",)):
            app_type = "graphql"
            language, framework = "python", "strawberry"
            reason = "Strawberry provides type-safe GraphQL with Python dataclass integration"
        elif any(w in desc_lower for w in ("desktop", "electron", "tauri")):
            app_type = "desktop"
            if "tauri" in desc_lower:
                language, framework = "rust", "tauri"
            else:
                language, framework = "typescript", "electron"
            reason = f"{framework} chosen for desktop: " + {
                "tauri": "Rust backend gives tiny binary size and native performance vs Electron",
                "electron": "full Chromium for complex UIs, massive npm ecosystem, cross-platform",
            }.get(framework, "best desktop framework for requirements")
        else:
            app_type = "web_app"
            language, framework = "python", "fastapi"
            reason = "FastAPI: async, auto docs, Pydantic validation — best default for web apps"

        # Determine database needs
        needs_db = any(w in desc_lower for w in ("database", "store", "persist", "user", "data",
                                                  "crud", "save", "record", "track", "manage"))
        db_choice = "postgresql" if needs_db else "none"
        if "mongo" in desc_lower:
            db_choice = "mongodb"
        elif "redis" in desc_lower:
            db_choice = "redis"
        elif "sqlite" in desc_lower:
            db_choice = "sqlite"

        # Determine auth needs
        needs_auth = any(w in desc_lower for w in ("auth", "login", "user", "sign up", "register",
                                                    "password", "jwt", "oauth", "session"))
        auth_strategy = "jwt" if needs_auth else "none"

        # Generate project using skills
        from nikto.skills.production import get_skill_function

        skill_map = {
            "rest_api": "skill_rest_api_builder",
            "mobile": "skill_mobile_app_builder",
            "cli": "skill_cli_builder",
            "bot": "skill_bot_builder",
            "smart_contract": "skill_solidity_builder",
            "game": "skill_lua_builder",
            "graphql": "skill_graphql_builder",
            "desktop": "skill_rust_builder" if language == "rust" else "skill_rest_api_builder",
            "web_app": "skill_rest_api_builder",
        }

        lang_skill_map = {
            "go": "skill_go_builder",
            "rust": "skill_rust_builder",
            "java": "skill_java_builder",
            "csharp": "skill_csharp_builder",
            "swift": "skill_swift_builder",
            "kotlin": "skill_kotlin_builder",
            "dart": "skill_flutter_builder",
            "solidity": "skill_solidity_builder",
            "lua": "skill_lua_builder",
        }

        skill_name = lang_skill_map.get(language, skill_map.get(app_type, "skill_rest_api_builder"))
        skill_fn = get_skill_function(skill_name)

        # Extract a project name from the description
        name_words = re.findall(r'\b[a-zA-Z]+\b', description)
        project_name = name_words[0].lower() if name_words else "myapp"
        if len(project_name) < 3:
            project_name = "myapp"

        output_dir = tempfile.mkdtemp(prefix="nicto_build_")

        kwargs = {"name": project_name, "output_dir": output_dir}
        if skill_name == "skill_rest_api_builder":
            kwargs["language"] = language
            kwargs["entities"] = project_name
        elif skill_name == "skill_mobile_app_builder":
            kwargs["framework"] = framework
        elif skill_name == "skill_bot_builder":
            kwargs["platform"] = "telegram" if "telegram" in desc_lower else "discord"
        elif skill_name == "skill_cli_builder":
            kwargs["language"] = language

        if skill_fn:
            scaffold_result = await skill_fn(**kwargs)
        else:
            scaffold_result = {"success": False, "output": f"Skill {skill_name} not found"}

        return {
            "app_type": app_type,
            "language": language,
            "framework": framework,
            "reason": reason,
            "database": db_choice,
            "auth": auth_strategy,
            "scaffold": json.loads(scaffold_result.get("output", "{}")) if scaffold_result.get("success") else {},
            "success": scaffold_result.get("success", False),
        }

    def detect_language(self, code_snippet: str) -> dict:
        """Detect the programming language, version hints, framework, and issues in a code snippet."""
        code = code_snippet.strip()
        language = "unknown"
        version = "unknown"
        framework = "none"
        issues = []

        # Language detection patterns (ordered by specificity)
        patterns = [
            # Rust
            (r'\bfn\s+\w+\s*\(.*\)\s*(->\s*\S+)?\s*\{', r'\blet\s+mut\b|\bimpl\b|\buse\s+\w+::', "rust"),
            # Go
            (r'\bfunc\s+\w+\s*\(', r'\bpackage\s+\w+|import\s+\(|:=|\bgo\s+\w+', "go"),
            # Swift
            (r'\bvar\s+\w+\s*:\s*\w+|\bfunc\s+\w+\(.*\)\s*->\s*\w+', r'\bimport\s+SwiftUI|\bstruct\s+\w+\s*:\s*View', "swift"),
            # Kotlin
            (r'\bfun\s+\w+\s*\(', r'\bval\s+\w+|\bvar\s+\w+\s*:\s*\w+|\bdata\s+class', "kotlin"),
            # Dart/Flutter
            (r'\bvoid\s+main\s*\(\s*\)\s*\{', r'\bWidget\s+build|\bStatelessWidget|\bStatefulWidget', "dart"),
            # TypeScript (before JS — must detect type annotations)
            (r':\s*(string|number|boolean|void|any)\b|\binterface\s+\w+\s*\{', r'\bimport\b.*from\s+["\']', "typescript"),
            # Java
            (r'\bpublic\s+(static\s+)?class\s+\w+', r'\bSystem\.out\.println|\bimport\s+java\.', "java"),
            # C#
            (r'\bnamespace\s+\w+|\busing\s+System', r'\bclass\s+\w+\s*:\s*\w+|\basync\s+Task', "csharp"),
            # C++
            (r'#include\s*<\w+>', r'\bstd::|cout|cin|namespace\s+\w+|template\s*<', "cpp"),
            # C
            (r'#include\s*<\w+\.h>', r'\bprintf\s*\(|\bmalloc\s*\(|\bvoid\s+\w+\s*\(', "c"),
            # Python
            (r'\bdef\s+\w+\s*\(|\bclass\s+\w+.*:', r'\bimport\s+\w+|\bfrom\s+\w+\s+import', "python"),
            # JavaScript
            (r'\bfunction\s+\w+\s*\(|\bconst\s+\w+\s*=', r'\bconsole\.log|\brequire\s*\(|\bexport\s+', "javascript"),
            # Ruby
            (r'\bdef\s+\w+\b', r'\bend\b.*\n.*\bend\b|\brequire\s+["\']|\bputs\b', "ruby"),
            # PHP
            (r'<\?php|\$\w+\s*=', r'\bfunction\s+\w+\s*\(|\becho\b|\b->\w+\(', "php"),
            # Solidity
            (r'\bpragma\s+solidity|\bcontract\s+\w+', r'\bmapping\s*\(|\bevent\s+\w+|\bmodifier\s+\w+', "solidity"),
            # SQL
            (r'\bSELECT\s+.*\bFROM\b|\bCREATE\s+TABLE\b', r'\bWHERE\b|\bINSERT\s+INTO\b|\bJOIN\b', "sql"),
            # Haskell
            (r'\bmodule\s+\w+|\bimport\s+\w+', r'\b::\s*\w+\s*->|\bdata\s+\w+\s*=|\bwhere\b', "haskell"),
            # Elixir
            (r'\bdefmodule\s+\w+|\bdef\s+\w+.*\bdo\b', r'\b|>\b|\bElixir\b|\bGenServer\b', "elixir"),
            # Lua
            (r'\bfunction\s+\w+\s*\(|\blocal\s+\w+\s*=', r'\bend\b|\brequire\s*\(|\blove\.\w+', "lua"),
            # PowerShell
            (r'\bfunction\s+\w+-\w+|\$\w+\s*=', r'\bGet-\w+|\bSet-\w+|\bInvoke-\w+|\bparam\s*\(', "powershell"),
            # Assembly
            (r'\bsection\s+\.\w+|\b(mov|push|pop|call|ret|jmp)\s+', r'\bsyscall\b|\bRSP\b|\bRAX\b', "assembly"),
        ]

        for primary, secondary, lang in patterns:
            if re.search(primary, code, re.MULTILINE):
                if re.search(secondary, code, re.MULTILINE):
                    language = lang
                    break

        # If no secondary matched, try primary only (less confident)
        if language == "unknown":
            for primary, _, lang in patterns:
                if re.search(primary, code, re.MULTILINE):
                    language = lang
                    break

        # Version detection
        version_patterns = {
            "python": [(r'python\s*(\d+\.\d+)', 1), (r'f["\']', None)],
            "javascript": [(r'const\s|let\s|=>\s', None)],
            "typescript": [(r'typescript.*?(\d+\.\d+)', 1)],
            "rust": [(r'edition\s*=\s*["\'](\d{4})["\']', 1)],
            "solidity": [(r'pragma\s+solidity\s*\^?(\d+\.\d+\.\d+)', 1)],
            "csharp": [(r'net(\d+\.\d+)', 1)],
            "go": [(r'go\s+(\d+\.\d+)', 1)],
        }
        for pat, group in version_patterns.get(language, []):
            m = re.search(pat, code)
            if m and group:
                version = m.group(group)
            elif m and group is None:
                if language == "python":
                    version = "3.6+"
                elif language == "javascript":
                    version = "ES6+"

        # Framework detection
        framework_patterns = {
            "python": [
                (r'from\s+fastapi|FastAPI\s*\(', "FastAPI"),
                (r'from\s+django|Django', "Django"),
                (r'from\s+flask|Flask\s*\(', "Flask"),
                (r'import\s+pytest|@pytest', "pytest"),
                (r'import\s+torch|from\s+torch', "PyTorch"),
            ],
            "javascript": [
                (r'from\s+["\']react["\']|React\.', "React"),
                (r'from\s+["\']vue["\']|createApp', "Vue.js"),
                (r'from\s+["\']express["\']|express\(\)', "Express"),
                (r'from\s+["\']next|getServerSideProps', "Next.js"),
            ],
            "typescript": [
                (r'from\s+["\']react["\']|React\.', "React"),
                (r'from\s+["\']@angular', "Angular"),
                (r'from\s+["\']@nestjs', "NestJS"),
            ],
            "dart": [
                (r'flutter|Widget|MaterialApp', "Flutter"),
            ],
            "kotlin": [
                (r'@Composable|Jetpack|MaterialTheme', "Jetpack Compose"),
                (r'SpringApplication|@Controller', "Spring Boot"),
            ],
            "swift": [
                (r'SwiftUI|@State|NavigationStack', "SwiftUI"),
                (r'UIViewController|UIKit', "UIKit"),
            ],
            "rust": [
                (r'axum::|Router::new', "Axum"),
                (r'actix_web|HttpServer', "Actix-web"),
                (r'tokio::|#\[tokio::main\]', "Tokio"),
            ],
            "go": [
                (r'gin\.|gin\.Default', "Gin"),
                (r'fiber\.|fiber\.New', "Fiber"),
                (r'echo\.|echo\.New', "Echo"),
            ],
            "java": [
                (r'@SpringBootApplication|@RestController', "Spring Boot"),
            ],
            "csharp": [
                (r'WebApplication\.CreateBuilder|\.MapControllers', "ASP.NET Core"),
                (r'EntityFrameworkCore|DbContext', "Entity Framework"),
            ],
            "solidity": [
                (r'@openzeppelin|OpenZeppelin', "OpenZeppelin"),
            ],
        }
        for pat, fw in framework_patterns.get(language, []):
            if re.search(pat, code, re.IGNORECASE):
                framework = fw
                break

        # Issue detection
        if language == "python":
            if re.search(r'except\s*:\s*\n\s*pass', code):
                issues.append("bare except with pass — silences all errors")
            if "eval(" in code:
                issues.append("eval() usage — security risk, consider alternatives")
            if re.search(r'import \*', code):
                issues.append("wildcard import — can cause namespace pollution")
        elif language in ("javascript", "typescript"):
            if "var " in code:
                issues.append("'var' is function-scoped — prefer 'const' or 'let'")
            if "== " in code and "=== " not in code:
                issues.append("loose equality (==) — use strict equality (===)")
        elif language == "c":
            if "gets(" in code:
                issues.append("gets() is unsafe — use fgets() instead")
            if "strcpy(" in code:
                issues.append("strcpy() can overflow — use strncpy() or strlcpy()")
        elif language == "solidity":
            if "tx.origin" in code:
                issues.append("tx.origin for auth is vulnerable to phishing")

        return {
            "language": language,
            "version": version,
            "framework": framework,
            "issues": issues,
        }

    async def translate_code(self, code: str, target_language: str) -> str:
        """Translate code from one language to another, preserving logic and using idiomatic patterns."""
        source = self.detect_language(code)
        src_lang = source["language"]
        tgt = target_language.lower().strip()

        # Normalize target language names
        tgt_map = {"js": "javascript", "ts": "typescript", "py": "python", "rb": "ruby",
                    "cs": "csharp", "c#": "csharp", "c++": "cpp", "golang": "go"}
        tgt = tgt_map.get(tgt, tgt)

        if src_lang == "unknown":
            return f"// Could not detect source language. Please specify.\n{code}"

        if src_lang == tgt:
            return f"// Source and target are the same language ({src_lang}).\n{code}"

        # Translation templates for common patterns
        translations = self._get_translation_map()
        key = f"{src_lang}_to_{tgt}"

        header = f"// Translated from {src_lang} to {tgt} by NICTO\n"
        header += f"// Original language: {src_lang}"
        if source["framework"] != "none":
            header += f" ({source['framework']})"
        header += "\n\n"

        # Try pattern-based translation for common constructs
        translated = self._translate_patterns(code, src_lang, tgt)
        if translated:
            return header + translated

        # Fallback: use LLM provider for translation
        prompt = (
            f"Translate the following {src_lang} code to idiomatic {tgt}. "
            f"Preserve the logic exactly. Use {tgt} idioms and best practices. "
            f"Add brief comments only where language-specific differences matter.\n\n"
            f"```{src_lang}\n{code}\n```\n\n"
            f"Output ONLY the translated {tgt} code, no explanations."
        )

        try:
            response = await self.provider.chat(
                messages=[
                    {"role": "system", "content": "You are a polyglot code translator. Output only code."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=4096,
            )
            result = response.get("content", "")
            # Strip markdown code fences if present
            result = re.sub(r'^```\w*\n', '', result)
            result = re.sub(r'\n```\s*$', '', result)
            return header + result
        except Exception:
            return header + self._basic_translate(code, src_lang, tgt)

    def _get_translation_map(self) -> dict:
        """Return common translation patterns between languages."""
        return {
            "print": {
                "python": "print({arg})",
                "javascript": "console.log({arg})",
                "typescript": "console.log({arg})",
                "go": 'fmt.Println({arg})',
                "rust": 'println!("{{}}", {arg})',
                "java": "System.out.println({arg})",
                "csharp": "Console.WriteLine({arg})",
                "kotlin": "println({arg})",
                "swift": "print({arg})",
                "cpp": "std::cout << {arg} << std::endl",
                "c": 'printf("%s\\n", {arg})',
                "ruby": "puts {arg}",
                "php": "echo {arg}",
            },
            "list_create": {
                "python": "[{items}]",
                "javascript": "[{items}]",
                "typescript": "[{items}]",
                "go": "[]interface{{}}{{{items}}}",
                "rust": "vec![{items}]",
                "java": "List.of({items})",
                "csharp": "new List<object> {{{items}}}",
                "kotlin": "listOf({items})",
                "swift": "[{items}]",
            },
            "for_loop": {
                "python": "for {var} in {iterable}:",
                "javascript": "for (const {var} of {iterable}) {{",
                "typescript": "for (const {var} of {iterable}) {{",
                "go": "for _, {var} := range {iterable} {{",
                "rust": "for {var} in {iterable} {{",
                "java": "for (var {var} : {iterable}) {{",
                "csharp": "foreach (var {var} in {iterable}) {{",
                "kotlin": "for ({var} in {iterable}) {{",
                "swift": "for {var} in {iterable} {{",
            },
        }

    def _translate_patterns(self, code: str, src: str, tgt: str) -> str:
        """Attempt pattern-based translation for simple code."""
        # Only handle very simple single-function translations
        lines = code.strip().split('\n')
        if len(lines) > 50:
            return ""  # Too complex for pattern-based translation

        # For simple print statements
        if len(lines) <= 3 and src == "python" and tgt == "javascript":
            translated_lines = []
            for line in lines:
                m = re.match(r'^print\((.+)\)$', line.strip())
                if m:
                    translated_lines.append(f"console.log({m.group(1)});")
                elif line.strip().startswith("#"):
                    translated_lines.append(line.replace("#", "//", 1))
                elif line.strip() == "":
                    translated_lines.append("")
                else:
                    return ""  # Can't handle this pattern
            if translated_lines:
                return "\n".join(translated_lines)

        return ""

    def _basic_translate(self, code: str, src: str, tgt: str) -> str:
        """Basic fallback translation with comments explaining differences."""
        comment_char = "//" if tgt not in ("python", "ruby", "powershell") else "#"
        result = f"{comment_char} NOTE: Automatic translation from {src} to {tgt}\n"
        result += f"{comment_char} Manual review recommended for idiomatic {tgt} patterns\n\n"

        if tgt == "python":
            result += f"# Original {src} code — translate manually:\n"
            for line in code.split('\n'):
                result += f"# {line}\n"
        elif tgt in ("javascript", "typescript", "go", "rust", "java", "csharp", "kotlin", "swift", "cpp", "c"):
            result += f"// Original {src} code — translate manually:\n"
            for line in code.split('\n'):
                result += f"// {line}\n"
        else:
            result += code

        return result

    def stop(self):
        self._running = False
        self.state = AgentState.DONE
