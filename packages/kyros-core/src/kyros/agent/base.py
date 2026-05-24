import asyncio, json, os, time, uuid
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Optional

import aiofiles

from kyros.config.settings import KyrosConfig, ModelConfig
from kyros.knowledge.loader import knowledge_base, search_knowledge
from kyros.memory.base import MemorySystem
from kyros.providers.base import create_provider
from kyros.tools.base import ToolResult, ToolRegistry


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
    def __init__(self, model=None, mode: AgentMode = AgentMode.INTERACTIVE, system_prompt: str = "You are KYROS, a modular AI agent."):
        self.model = model or KyrosConfig().model
        self.mode = mode
        self.system_prompt = system_prompt
        self.max_tokens = 4096
        self.temperature = 0.5


class Agent:
    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.id = str(uuid.uuid4())[:12]
        self.state = AgentState.IDLE
        model_cfg = self.config.model if isinstance(self.config.model, ModelConfig) else ModelConfig(model=self.config.model if isinstance(self.config.model, str) else "local")
        self.provider = create_provider(model_cfg)
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
        await self.memory.store(result.get("content", ""), source="kyros")
        self.state = AgentState.IDLE
        return result

    async def run_sync(self, prompt: str) -> str:
        result = await self.run(prompt)
        return result.get("content", "")

    def get_status(self) -> dict:
        info = self.provider.get_info()
        return {"id": self.id, "state": self.state.value, "mode": self.config.mode.value if hasattr(self.config.mode, 'value') else str(self.config.mode), "provider": info}

    async def build_app(self, spec: dict) -> dict:
        app_type = spec.get("type", "web")
        name = spec.get("name", "myapp")
        framework = spec.get("framework", "fastapi")
        features = spec.get("features", [])
        output_dir = spec.get("output_dir", os.path.join(os.getcwd(), name))

        known_templates = {
            "fastapi": {"files": {"pyproject.toml": '[project]\nname = "{name}"\nversion = "0.1.0"\ndependencies = ["fastapi", "uvicorn"]', "app/main.py": 'from fastapi import FastAPI\n\napp = FastAPI(title="{name}")\n\n@app.get("/")\ndef root():\n    return {"message": "Hello from {name}"}'}, "entry": "app/main.py"},
            "react": {"files": {"package.json": '{{\n  "name": "{name}",\n  "version": "0.1.0",\n  "dependencies": {{"react": "^18", "react-dom": "^18"}}\n}}', "src/App.jsx": 'import React from "react";\n\nexport default function App() {\n  return <div>Hello from {name}</div>;\n}'}, "entry": "src/App.jsx"},
            "flask": {"files": {"pyproject.toml": '[project]\nname = "{name}"\nversion = "0.1.0"\ndependencies = ["flask"]', "app.py": 'from flask import Flask\n\napp = Flask(__name__)\n\n@app.route("/")\ndef home():\n    return "Hello from {name}"'}, "entry": "app.py"},
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
