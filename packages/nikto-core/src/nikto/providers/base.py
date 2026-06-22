"""
Model Provider Module for NIKTO.

Supports OpenAI, Anthropic Claude, Ollama, and local llama.cpp providers.
Auto-detection: if OPENAI_API_KEY is set → use OpenAI.
If ANTHROPIC_API_KEY is set → use Claude. Else → use local/fallback.
"""

import json
import os
from typing import Any, Optional

from nikto.config.settings import ModelConfig


class ModelProvider:
    """Abstract base for LLM providers."""

    def __init__(self, config: ModelConfig) -> None:
        self.config = config

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        """Send a chat completion request."""
        raise NotImplementedError

    async def stream_chat(self, messages: list[dict[str, str]], **kwargs: Any) -> Any:
        """Stream a chat completion."""
        raise NotImplementedError


class OpenAIProvider(ModelProvider):
    """OpenAI / compatible API provider."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)
        self._client: Any = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            from openai import AsyncOpenAI
            api_key = self.config.api_key or os.environ.get("OPENAI_API_KEY", "")
            base_url = self.config.api_base or os.environ.get("OPENAI_BASE_URL", "")
            kwargs: dict[str, Any] = {"api_key": api_key}
            if base_url:
                kwargs["base_url"] = base_url
            self._client = AsyncOpenAI(**kwargs)
        except ImportError:
            self._client = None

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        if self._client is None:
            return {"content": "[OpenAI provider unavailable: install openai package]", "finish_reason": "error"}
        model = kwargs.pop("model", self.config.model or "gpt-4o")
        try:
            resp = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs,
            )
            choice = resp.choices[0]
            return {"content": choice.message.content or "", "finish_reason": choice.finish_reason or "stop"}
        except Exception as e:
            return {"content": f"[OpenAI Error] {e}", "finish_reason": "error"}

    async def stream_chat(self, messages: list[dict[str, str]], **kwargs: Any) -> Any:
        if self._client is None:
            return
        model = kwargs.pop("model", self.config.model or "gpt-4o")
        try:
            stream = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **kwargs,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        except Exception:
            return


class AnthropicProvider(ModelProvider):
    """Anthropic Claude provider."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)
        self._client: Any = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            from anthropic import AsyncAnthropic
            api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
            self._client = AsyncAnthropic(api_key=api_key)
        except ImportError:
            self._client = None

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        if self._client is None:
            return {"content": "[Anthropic provider unavailable: install anthropic package]", "finish_reason": "error"}
        model = kwargs.pop("model", self.config.model or "claude-sonnet-4-20250514")
        try:
            system_msg = None
            chat_messages = messages
            if messages and messages[0].get("role") == "system":
                system_msg = messages[0]["content"]
                chat_messages = messages[1:]
            resp = await self._client.messages.create(
                model=model,
                system=system_msg,
                messages=chat_messages,
                **kwargs,
            )
            return {"content": resp.content[0].text if resp.content else "", "finish_reason": "stop"}
        except Exception as e:
            return {"content": f"[Anthropic Error] {e}", "finish_reason": "error"}

    async def stream_chat(self, messages: list[dict[str, str]], **kwargs: Any) -> Any:
        if self._client is None:
            return
        model = kwargs.pop("model", self.config.model or "claude-sonnet-4-20250514")
        try:
            system_msg = None
            chat_messages = messages
            if messages and messages[0].get("role") == "system":
                system_msg = messages[0]["content"]
                chat_messages = messages[1:]
            async with self._client.messages.stream(
                model=model,
                system=system_msg,
                messages=chat_messages,
                **kwargs,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception:
            return


class OllamaProvider(ModelProvider):
    """Ollama local provider."""

    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)
        self._client: Any = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            from ollama import AsyncClient
            host = self.config.ollama_host or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
            self._client = AsyncClient(host=host)
        except ImportError:
            self._client = None

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        if self._client is None:
            return {"content": "[Ollama unavailable: install ollama package]", "finish_reason": "error"}
        model = kwargs.pop("model", self.config.ollama_model or "llama3.2:1b")
        try:
            resp = await self._client.chat(model=model, messages=messages, **kwargs)
            return {"content": resp["message"]["content"], "finish_reason": "stop"}
        except Exception as e:
            return {"content": f"[Ollama Error] {e}", "finish_reason": "error"}

    async def stream_chat(self, messages: list[dict[str, str]], **kwargs: Any) -> Any:
        if self._client is None:
            return
        model = kwargs.pop("model", self.config.ollama_model or "llama3.2:1b")
        try:
            async for part in await self._client.chat(model=model, messages=messages, stream=True, **kwargs):
                yield part["message"]["content"]
        except Exception:
            return


class LocalProvider(ModelProvider):
    """Local / fallback provider (no real LLM)."""

    async def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        return {"content": "[Local provider: no LLM connected]", "finish_reason": "stop"}

    async def stream_chat(self, messages: list[dict[str, str]], **kwargs: Any) -> Any:
        yield "[Local provider: no LLM connected]"


def create_provider(config: ModelConfig) -> ModelProvider:
    """Auto-detect and create the appropriate provider.

    Resolution order:
    1. Explicit ``config.provider`` (``"openai"``, ``"anthropic"``, ``"ollama"``, ``"local"``)
    2. ``OPENAI_API_KEY`` env var → OpenAI
    3. ``ANTHROPIC_API_KEY`` env var → Anthropic
    4. Fall back to local
    """
    provider_name = (config.provider or "").lower()

    if not provider_name or provider_name == "auto":
        if os.environ.get("OPENAI_API_KEY", ""):
            provider_name = "openai"
        elif os.environ.get("ANTHROPIC_API_KEY", ""):
            provider_name = "anthropic"
        else:
            provider_name = "local"

    if provider_name == "openai":
        return OpenAIProvider(config)
    elif provider_name == "anthropic":
        return AnthropicProvider(config)
    elif provider_name == "ollama":
        return OllamaProvider(config)
    else:
        return LocalProvider(config)
