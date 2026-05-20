"""Provider factory — creates the best available inference engine."""
import asyncio, json, logging
from typing import Any, AsyncGenerator, Optional

from nikto.config.settings import ModelConfig
from nikto.providers.dual import DualEngineProvider
from nikto.providers.chatml import format_chatml, extract_response, count_tokens

logger = logging.getLogger(__name__)


class ModelProvider:
    """Unified provider wrapping DualEngineProvider for backwards compatibility."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.engine = DualEngineProvider(config)
        self.messages: list[dict] = []

    async def chat(
        self, messages: list[dict], tools: Optional[list[dict]] = None,
        temperature: float = 0.5, max_tokens: int = 4096,
    ) -> dict:
        """Chat with message history. Uses dual engine (online/offline)."""
        # Extract system prompt
        system = ""
        user_input = ""
        history = []
        for m in messages:
            role = m.get("role", "")
            content = m.get("content", "")
            if role == "system":
                system = content
            elif role == "user":
                user_input = content
                history.append((content, ""))
            elif role == "assistant":
                if history:
                    prev_user, _ = history[-1]
                    history[-1] = (prev_user, content)

        result = await self.engine.chat(
            user_input=user_input or messages[-1].get("content", "") if messages else "",
            system_prompt=system or "You are NIKTO, a helpful AI assistant.",
            conversation_history=history if len(history) > 1 else None,
            max_tokens=min(max_tokens, 4096),
            temperature=temperature,
        )

        return {"content": result.get("content", ""), "tool_calls": []}

    async def stream_chat(
        self, messages: list[dict], tools: Optional[list[dict]] = None,
        temperature: float = 0.5, max_tokens: int = 4096,
    ) -> AsyncGenerator[dict, None]:
        """Stream chat response."""
        # Extract system and user message
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_input = messages[-1].get("content", "") if messages else ""

        collected = ""
        async for text in self.engine.chat_stream(
            user_input=user_input,
            system_prompt=system or "You are NIKTO, a helpful AI assistant.",
            max_tokens=min(max_tokens, 4096),
            temperature=temperature,
        ):
            collected += text
            yield {"type": "content", "content": text}

        yield {"type": "done", "content": ""}

    def get_info(self) -> dict:
        return self.engine.get_info()


def create_provider(config: ModelConfig) -> ModelProvider:
    return ModelProvider(config)
