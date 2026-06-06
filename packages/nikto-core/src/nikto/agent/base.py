import asyncio, json, os, time, uuid
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Optional

import aiofiles

from nikto.brain.core import NiktoBrain
from nikto.config.settings import NiktoConfig, ModelConfig
from nikto.knowledge.loader import knowledge_base, search_knowledge
from nikto.providers.base import create_provider
from nikto.tools.base import ToolResult, ToolRegistry
from nikto.voice.engine import VoiceEngine


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
    def __init__(self, model=None, mode: AgentMode = AgentMode.INTERACTIVE, system_prompt: str = "You are NIKTO, a highly capable AI assistant."):
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
        self.brain = None
        self.provider = None
        self.memory = MemorySystem()
        self.tool_registry = ToolRegistry()
        self.voice = VoiceEngine()

    async def awaken_brain(self):
        self.brain = NiktoBrain()
        await self.brain.awaken()
        self.brain.knowledge.add_fact(
            f"Agent {self.id} initialized with mode {self.config.mode.value}",
            source="system",
            confidence=1.0,
        )
        return self

    async def run(self, task: str, stream: bool = False) -> dict:
        self.state = AgentState.THINKING

        if self.brain is None:
            await self.awaken_brain()

        result = self.brain.process(task, {"mode": self.config.mode.value})
        thought = result["thought"]["content"]

        await self.memory.store(task, source="user")
        await self.memory.store(thought, source="nikto_brain")
        self.state = AgentState.IDLE

        return {"content": thought, "brain_state": self.brain.get_status(), "metacognition": result.get("metacognition")}

    async def run_sync(self, prompt: str) -> str:
        result = await self.run(prompt)
        return result.get("content", "")

    def get_status(self) -> dict:
        if self.brain:
            return {"id": self.id, "state": self.state.value, "mode": self.config.mode.value if hasattr(self.config.mode, 'value') else str(self.config.mode), "brain": self.brain.get_status()}
        return {"id": self.id, "state": self.state.value, "mode": self.config.mode.value if hasattr(self.config.mode, 'value') else str(self.config.mode), "brain": "uninitialized"}

    async def build_app(self, spec: dict) -> dict:
        app_type = spec.get("type", "web")
        name = spec.get("name", "myapp")
        framework = spec.get("framework", "fastapi")
        features = spec.get("features", [])
        output_dir = spec.get("output_dir", os.path.join(os.getcwd(), name))

        _fastapi_pyproject = (
            '[project]\nname = "{name}"\nversion = "0.1.0"\n'
            'dependencies = ["fastapi", "uvicorn"]'
        )
        _fastapi_main = (
            'from fastapi import FastAPI\n\n'
            'app = FastAPI(title="{name}")\n\n'
            '@app.get("/")\n'
            'def root():\n'
            '    return {"message": "Hello from {name}"}'
        )
        _react_package = (
            '{\n'
            '  "name": "{name}",\n'
            '  "version": "0.1.0",\n'
            '  "dependencies": {"react": "^18", "react-dom": "^18"}\n'
            '}'
        )
        _react_app = (
            'import React from "react";\n\n'
            'export default function App() {\n'
            '  return <div>Hello from {name}</div>;\n'
            '}'
        )
        _flask_pyproject = (
            '[project]\nname = "{name}"\nversion = "0.1.0"\n'
            'dependencies = ["flask"]'
        )
        _flask_app = (
            'from flask import Flask\n\n'
            'app = Flask(__name__)\n\n'
            '@app.route("/")\n'
            'def home():\n'
            '    return "Hello from {name}"'
        )
        known_templates = {
            "fastapi": {
                "files": {
                    "pyproject.toml": _fastapi_pyproject,
                    "app/main.py": _fastapi_main,
                },
                "entry": "app/main.py",
            },
            "react": {
                "files": {
                    "package.json": _react_package,
                    "src/App.jsx": _react_app,
                },
                "entry": "src/App.jsx",
            },
            "flask": {
                "files": {
                    "pyproject.toml": _flask_pyproject,
                    "app.py": _flask_app,
                },
                "entry": "app.py",
            },
        }

        template = known_templates.get(framework, known_templates["fastapi"])
        knowledge = await search_knowledge(f"{framework} framework project structure")
        files_created = []

        os.makedirs(output_dir, exist_ok=True)
        for rel_path, content_template in template["files"].items():
            full_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            content = content_template.replace("{name}", name)
            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(content)
            files_created.append(full_path)

        readme_path = os.path.join(output_dir, "README.md")
        readme_content = f"# {name}\n\nAutomatically generated {app_type} project using {framework}.\n\n## Features\n" + "\n".join(f"- {f}" for f in features) + "\n"
        async with aiofiles.open(readme_path, "w", encoding="utf-8") as f:
            await f.write(readme_content)
        files_created.append(readme_path)

        return {
            "success": True,
            "project_path": output_dir,
            "files_created": files_created,
            "framework": framework,
            "features": features,
        }

    async def detect_language(self, text: str) -> dict:
        try:
            from langdetect import detect, detect_langs
            langs = detect_langs(text)
            best = langs[0]
            lang_code = best.lang
            confidence = best.prob
        except ImportError:
            lang_code = "en"
            confidence = 0.5
            cjk = sum(1 for c in text if '\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u30ff' or '\uac00' <= c <= '\ud7af')
            cyrillic = sum(1 for c in text if '\u0400' <= c <= '\u04ff')
            arabic = sum(1 for c in text if '\u0600' <= c <= '\u06ff')
            hebrew = sum(1 for c in text if '\u0590' <= c <= '\u05ff')
            thai = sum(1 for c in text if '\u0e00' <= c <= '\u0e7f')
            devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097f')
            total = len(text) + 1
            scores = {"zh": cjk, "ru": cyrillic, "ar": arabic, "he": hebrew, "th": thai, "hi": devanagari}
            detected = [(s, k) for k, s in scores.items() if s / total > 0.05]
            if detected:
                best = max(detected)
                lang_code = best[1]
                confidence = best[0] / total

        language_map = {
            "en": "English", "es": "Spanish", "fr": "French", "de": "German",
            "zh": "Chinese", "ja": "Japanese", "ko": "Korean", "ar": "Arabic",
            "ru": "Russian", "pt": "Portuguese", "it": "Italian", "nl": "Dutch",
            "pl": "Polish", "tr": "Turkish", "sv": "Swedish", "da": "Danish",
            "no": "Norwegian", "fi": "Finnish", "el": "Greek", "he": "Hebrew",
            "hi": "Hindi", "th": "Thai", "vi": "Vietnamese", "id": "Indonesian",
            "ms": "Malay",
        }
        script_map = {
            "en": "Latin", "es": "Latin", "fr": "Latin", "de": "Latin",
            "zh": "Han", "ja": "Kana", "ko": "Hangul", "ar": "Arabic",
            "ru": "Cyrillic", "pt": "Latin", "it": "Latin", "nl": "Latin",
            "pl": "Latin", "tr": "Latin", "sv": "Latin", "da": "Latin",
            "no": "Latin", "fi": "Latin", "el": "Greek", "he": "Hebrew",
            "hi": "Devanagari", "th": "Thai", "vi": "Latin", "id": "Latin",
            "ms": "Latin",
        }
        return {
            "language": language_map.get(lang_code, "Unknown"),
            "code": lang_code,
            "confidence": round(confidence, 4),
            "script": script_map.get(lang_code, "Unknown"),
        }

    async def translate_code(self, code: str, from_lang: str, to_lang: str) -> dict:
        if from_lang == to_lang:
            return {"translated_code": code, "from_lang": from_lang, "to_lang": to_lang, "preserved_semantics": True}

        system_prompt = f"Translate the following source code from {from_lang} to {to_lang}. Preserve all comments, string literals, and logic exactly. Output ONLY the translated code with no additional text."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"```\n{code}\n```"},
        ]
        result = await self.provider.chat(messages, max_tokens=self.config.max_tokens, temperature=0.2)
        translated = result.get("content", "").strip()
        translated = translated.removeprefix("```" + to_lang).removeprefix("```").removesuffix("```").strip()
        return {"translated_code": translated, "from_lang": from_lang, "to_lang": to_lang, "preserved_semantics": True}