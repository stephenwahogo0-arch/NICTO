"""Dual-engine switching — online API / offline GGUF with automatic failover."""

import logging
import time
from typing import AsyncGenerator, Optional

import httpx

from kyros.config.settings import ModelConfig
from kyros.providers.llamacpp import LLaMACPPProvider
from kyros.providers.chatml import (
    format_chatml_with_context,
    extract_response,
    count_tokens,
)

logger = logging.getLogger(__name__)


class DualEngineProvider:
    """Switches between online API and local GGUF inference.
    
    Online mode: Routes to external API (zero local heat, full capability)
    Offline mode: Uses local llama.cpp GGUF engine (private, air-gapped)
    
    Automatic switching based on network availability.
    """

    def __init__(self, config: ModelConfig):
        self.config = config
        self.local = LLaMACPPProvider(config)
        self._online_available = None
        self._last_online_check = 0
        self.current_mode = "local"  # 'local' or 'online'

    async def _check_online(self) -> bool:
        """Check if online API is available (cached for 30s)."""
        now = time.time()
        if now - self._last_online_check < 30 and self._online_available is not None:
            return self._online_available
        self._last_online_check = now

        if not self.config.api_base:
            self._online_available = False
            return False

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.config.api_base}/health")
                self._online_available = resp.status_code == 200
        except Exception:
            self._online_available = False

        return self._online_available

    async def chat(
        self,
        user_input: str,
        system_prompt: str,
        conversation_history: list[tuple[str, str]] = None,
        memory_context: str = "",
        max_tokens: int = 512,
        temperature: Optional[float] = None,
        force_local: bool = False,
    ) -> dict:
        """Generate response using best available engine."""
        temp = temperature if temperature is not None else self.config.temperature or 0.5
        temp = max(0.3, min(temp, 0.7))

        # Try online first if not forced local
        online_ok = False
        if not force_local:
            online_ok = await self._check_online()
        
        if online_ok:
            self.current_mode = "online"
            return await self._online_chat(
                user_input, system_prompt, conversation_history,
                memory_context, max_tokens, temp
            )

        # Fall back to local GGUF
        self.current_mode = "local"
        return await self._local_chat(
            user_input, system_prompt, conversation_history,
            memory_context, max_tokens, temp
        )

    async def _online_chat(self, user_input, system_prompt, history, memory, max_tokens, temp) -> dict:
        """Chat via remote API."""
        prompt = format_chatml_with_context(user_input, system_prompt, history, memory)
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                payload = {
                    "model": self.config.model or "llama3.2:1b",
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temp,
                    "stream": False,
                }
                resp = await client.post(
                    f"{self.config.api_base}/api/generate",
                    json=payload,
                )
                data = resp.json()
                content = data.get("response", "").strip()
                return {
                    "content": content,
                    "tokens_used": data.get("eval_count", 0),
                    "mode": "online",
                    "tier": "cloud",
                }
        except Exception as e:
            logger.warning(f"Online chat failed: {e}, falling back to local")
            return await self._local_chat(user_input, system_prompt, history, memory, max_tokens, temp)

    async def _local_chat(self, user_input, system_prompt, history, memory, max_tokens, temp) -> dict:
        """Chat via local GGUF engine."""
        prompt = format_chatml_with_context(user_input, system_prompt, history, memory)

        result = await self.local.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temp,
        )

        content = result.get("content", "")
        backend = result.get("backend", "none")
        tokens = result.get("tokens_used", 0)

        # If we got the "need model" message, try to extract any useful fallback
        if "KYROS needs a local LLM" in content:
            return {
                "content": content,
                "tokens_used": 0,
                "mode": "local",
                "tier": "no_model",
            }

        # Clean up response
        content = extract_response(content)

        tier = "tier1"
        if "llama_cpp" in backend:
            import os
            ram = os.cpu_count() or 4
            tier = "tier2" if ram >= 8 else "tier1"

        return {
            "content": content,
            "tokens_used": tokens,
            "mode": "local",
            "tier": tier,
            "backend": backend,
        }

    async def chat_stream(
        self, user_input, system_prompt, history=None, memory="",
        max_tokens=512, temperature=None, force_local=False,
    ):
        """Stream response tokens."""
        temp = temperature if temperature is not None else self.config.temperature or 0.5
        temp = max(0.3, min(temp, 0.7))

        online_ok = False
        if not force_local:
            online_ok = await self._check_online()

        if online_ok:
            prompt = format_chatml_with_context(user_input, system_prompt, history, memory)
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    async with client.stream(
                        "POST", f"{self.config.api_base}/api/generate",
                        json={"model": self.config.model or "llama3.2:1b", "prompt": prompt,
                              "max_tokens": max_tokens, "temperature": temp, "stream": True},
                    ) as resp:
                        async for line in resp.aiter_lines():
                            if line.strip():
                                import json as _json
                                try:
                                    data = _json.loads(line)
                                    text = data.get("response", "")
                                    if text:
                                        yield text
                                except Exception:
                                    pass
                return
            except Exception:
                pass

        async for text in self.local.stream_generate(
            format_chatml_with_context(user_input, system_prompt, history, memory),
            max_tokens=max_tokens, temperature=temp,
        ):
            yield text

    def is_local_available(self) -> bool:
        return self.local.is_available()

    def get_info(self) -> dict:
        """Get engine status information."""
        return {
            "mode": self.current_mode,
            "local_available": self.local.is_available(),
            "model_path": str(self.local.model_path) if self.local.model_path else None,
            "threads": self.local.n_threads,
            "gpu_layers": self.local.n_gpu_layers,
            "context_size": self.local.ctx_size,
            "temperature": self.local.temperature,
        }
