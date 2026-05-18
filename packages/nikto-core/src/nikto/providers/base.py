import json
from typing import Any, AsyncGenerator, Optional

from nikto.config.settings import ModelConfig


class ModelProvider:
    def __init__(self, config: ModelConfig):
        self.config = config

    async def chat(
        self, messages: list[dict], tools: Optional[list[dict]] = None,
        temperature: float = 0.2, max_tokens: int = 64000,
    ) -> dict:
        raise NotImplementedError

    async def stream_chat(
        self, messages: list[dict], tools: Optional[list[dict]] = None,
        temperature: float = 0.2, max_tokens: int = 64000,
    ) -> AsyncGenerator[dict, None]:
        raise NotImplementedError
        yield  # pragma: no cover


class LiteLLMProvider(ModelProvider):
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        try:
            import litellm
            from litellm import acompletion
            self.litellm = litellm
            self.acompletion = acompletion
        except ImportError:
            raise ImportError("litellm is required. Install with: uv pip install litellm")

        self.model_name = config.model
        if config.api_key:
            self._set_api_key(config)

    def _set_api_key(self, config: ModelConfig):
        provider_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "kimi": "MOONSHOT_API_KEY",
            "groq": "GROQ_API_KEY",
            "perplexity": "PERPLEXITYAI_API_KEY",
            "ollama": None,
        }
        env_var = provider_map.get(config.provider)
        if env_var:
            import os
            os.environ[env_var] = config.api_key

    async def chat(
        self, messages: list[dict], tools: Optional[list[dict]] = None,
        temperature: float = 0.2, max_tokens: int = 64000,
    ) -> dict:
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools

        if self.config.api_base:
            kwargs["api_base"] = self.config.api_base

        try:
            resp = await self.acompletion(**kwargs)
            choice = resp.choices[0]
            msg = choice.message

            result = {"content": msg.content or ""}
            if msg.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]

            usage = getattr(resp, "usage", None)
            if usage:
                result["usage"] = {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                }
            return result
        except Exception as e:
            return {"content": f"Error: {str(e)}"}

    async def stream_chat(
        self, messages: list[dict], tools: Optional[list[dict]] = None,
        temperature: float = 0.2, max_tokens: int = 64000,
    ) -> AsyncGenerator[dict, None]:
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
        if self.config.api_base:
            kwargs["api_base"] = self.config.api_base

        try:
            stream = await self.acompletion(**kwargs)
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else {}
                result = {}
                if delta.content:
                    result["content"] = delta.content
                    result["type"] = "content"
                if delta.tool_calls:
                    result["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name if tc.function else None,
                                "arguments": tc.function.arguments if tc.function else "",
                            },
                        }
                        for tc in delta.tool_calls
                    ]
                    result["type"] = "tool_call"
                if result:
                    yield result
        except Exception as e:
            yield {"type": "error", "content": str(e)}


def create_provider(config: ModelConfig) -> ModelProvider:
    return LiteLLMProvider(config)
