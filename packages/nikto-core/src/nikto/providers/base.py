import asyncio, json, logging
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
    """Real local LLM via Ollama. No templates, no fakes.
    If Ollama is not installed, tells the user how to install it."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.model = config.ollama_model or "llama3"
        self.host = config.ollama_host or "http://127.0.0.1:11434"
        self._ollama_available = None
        self._ollama_models = []

    async def _check_ollama(self) -> bool:
        if self._ollama_available is not None:
            return self._ollama_available
        # Check via HTTP ping first (works on all platforms)
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3) as client:
                resp = await client.get(f"{self.host}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    self._ollama_models = [m["name"] for m in data.get("models", [])]
                    self._ollama_available = True
                    logger.info(f"Ollama detected at {self.host}. Models: {self._ollama_models}")
                    return True
        except Exception:
            pass
        # Fallback: check if ollama binary exists
        try:
            proc = await asyncio.create_subprocess_exec(
                "ollama", "--version",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(proc.communicate(), timeout=5)
            self._ollama_available = proc.returncode == 0
            if self._ollama_available:
                logger.info(f"Ollama binary detected (model: {self.model})")
            return self._ollama_available
        except Exception:
            self._ollama_available = False
            logger.info("Ollama not found")
            return False

    async def chat(
        self, messages: list[dict], tools: Optional[list[dict]] = None,
        temperature: float = 0.7, max_tokens: int = 65536,
    ) -> dict:
        if await self._check_ollama():
            return await self._ollama_chat(messages, tools, temperature, max_tokens)
        return self._need_ollama_response()

    async def stream_chat(
        self, messages: list[dict], tools: Optional[list[dict]] = None,
        temperature: float = 0.7, max_tokens: int = 65536,
    ) -> AsyncGenerator[dict, None]:
        if await self._check_ollama():
            async for chunk in self._ollama_stream(messages, tools, temperature, max_tokens):
                yield chunk
        else:
            resp = self._need_ollama_response()
            yield {"type": "content", "content": resp["content"]}
            yield {"type": "done", "content": ""}

    async def _ollama_chat(self, messages, tools, temperature, max_tokens) -> dict:
        try:
            import httpx
            if self.model not in self._ollama_models:
                # Model not pulled yet
                return {"content": f"The model '{self.model}' is not available in Ollama. Run: ollama pull {self.model}"}

            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }
            if tools:
                payload["tools"] = self._convert_tools(tools)

            async with httpx.AsyncClient(timeout=300) as client:
                resp = await client.post(f"{self.host}/api/chat", json=payload)
                data = resp.json()
            return {"content": data.get("message", {}).get("content", "")}
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return {"content": f"Ollama error: {e}. Start Ollama with: ollama serve"}

    async def _ollama_stream(self, messages, tools, temperature, max_tokens) -> AsyncGenerator:
        try:
            import httpx
            if self.model not in self._ollama_models:
                yield {"type": "content", "content": f"Run: ollama pull {self.model}"}
                yield {"type": "done", "content": ""}
                return

            payload = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": {"temperature": temperature, "num_predict": max_tokens},
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

    def _need_ollama_response(self) -> dict:
        return {
            "content": (
                "NIKTO needs a local LLM to run. Install Ollama (free, open-source):\n\n"
                "1. Download from https://ollama.com\n"
                "2. Run: ollama pull llama3\n"
                "3. Run: ollama serve\n"
                "4. Restart NIKTO\n\n"
                "Ollama runs completely offline. No internet needed after download."
            )
        }

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
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
