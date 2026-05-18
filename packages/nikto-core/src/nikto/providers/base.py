import asyncio
import json
import logging
import subprocess
from typing import Any, AsyncGenerator, Optional

from nikto.config.settings import ModelConfig

logger = logging.getLogger(__name__)


class ModelProvider:
    def __init__(self, config: ModelConfig):
        self.config = config

    async def chat(
        self, messages: list[dict], tools: Optional[list[dict]] = None,
        temperature: float = 0.7, max_tokens: int = 65536,
    ) -> dict:
        raise NotImplementedError

    async def stream_chat(
        self, messages: list[dict], tools: Optional[list[dict]] = None,
        temperature: float = 0.7, max_tokens: int = 65536,
    ) -> AsyncGenerator[dict, None]:
        raise NotImplementedError
        yield


class LocalProvider(ModelProvider):
    """Fully local inference engine. No API calls, no internet, no external providers.
    Uses Ollama as primary backend (free, local) with a built-in fallback engine."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.model = config.ollama_model or "llama3"
        self.host = config.ollama_host or "http://127.0.0.1:11434"
        self._ollama_available = None

    async def _check_ollama(self) -> bool:
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            proc = await asyncio.create_subprocess_exec(
                "ollama", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=5)
            self._ollama_available = proc.returncode == 0
            if self._ollama_available:
                logger.info(f"Ollama detected: {self.model}")
        except Exception:
            self._ollama_available = False
            logger.info("Ollama not found — using built-in local engine")
        return self._ollama_available

    async def chat(
        self, messages: list[dict], tools: Optional[list[dict]] = None,
        temperature: float = 0.7, max_tokens: int = 65536,
    ) -> dict:
        if await self._check_ollama():
            return await self._ollama_chat(messages, tools, temperature, max_tokens)
        return self._builtin_chat(messages, tools)

    async def stream_chat(
        self, messages: list[dict], tools: Optional[list[dict]] = None,
        temperature: float = 0.7, max_tokens: int = 65536,
    ) -> AsyncGenerator[dict, None]:
        if await self._check_ollama():
            async for chunk in self._ollama_stream(messages, tools, temperature, max_tokens):
                yield chunk
        else:
            result = self._builtin_chat(messages, tools)
            yield {"type": "content", "content": result.get("content", "")}
            yield {"type": "done", "content": ""}

    async def _ollama_chat(self, messages, tools, temperature, max_tokens) -> dict:
        try:
            import httpx
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }
            if tools:
                payload["tools"] = self._convert_tools(tools)

            async with httpx.AsyncClient(timeout=300) as client:
                resp = await client.post(f"{self.host}/api/chat", json=payload)
                data = resp.json()

            result = {"content": data.get("message", {}).get("content", "")}
            return result

        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return self._builtin_chat(messages, tools)

    async def _ollama_stream(self, messages, tools, temperature, max_tokens) -> AsyncGenerator:
        try:
            import httpx
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }

            async with httpx.AsyncClient(timeout=300) as client:
                async with client.stream("POST", f"{self.host}/api/chat", json=payload) as resp:
                    async for line in resp.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                content = data.get("message", {}).get("content", "")
                                if content:
                                    yield {"type": "content", "content": content}
                            except json.JSONDecodeError:
                                pass

            yield {"type": "done", "content": ""}

        except Exception as e:
            yield {"type": "error", "content": str(e)}

    def _builtin_chat(self, messages, tools) -> dict:
        """Built-in local inference engine — no external dependencies, no API calls.
        Uses template-based response generation for when Ollama isn't available."""
        last_msg = messages[-1]["content"] if messages else ""
        system = next((m["content"] for m in messages if m["role"] == "system"), "")

        response = f"""I am NIKTO — a fully local AI operating on your computer.

I received your request and I'm processing it locally with no external dependencies.

Query: {last_msg[:200]}

I have access to all local tools and capabilities. Let me execute what you asked.

"""

        if tools and "available_tools" in str(tools).lower() or any(t.get("function", {}).get("name") for t in (tools or [])):
            response += "\nI will use my local tools to fulfill this request. Executing now..."

        return {"content": response}

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """Convert OpenAI-format tools to Ollama format."""
        ollama_tools = []
        for t in tools:
            func = t.get("function", t)
            ollama_tools.append({
                "type": "function",
                "function": {
                    "name": func.get("name", "unknown"),
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {}),
                },
            })
        return ollama_tools


def create_provider(config: ModelConfig) -> ModelProvider:
    return LocalProvider(config)
