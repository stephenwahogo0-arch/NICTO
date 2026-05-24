import os
import json
import logging
from typing import Optional, AsyncGenerator
from uuid import uuid4

from kyros.config.settings import ModelConfig

logger = logging.getLogger(__name__)


class AnthropicProvider:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.api_key = config.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = config.model or "claude-sonnet-4-20250514"

    async def chat(self, messages: list[dict], **kwargs) -> dict:
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.api_key)
            msg = await client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.5),
                messages=[m for m in messages if m["role"] != "system"],
                system=next((m["content"] for m in messages if m["role"] == "system"), None),
            )
            return {"content": msg.content[0].text if msg.content else "", "tokens_used": msg.usage.output_tokens if msg.usage else 0, "mode": "anthropic", "provider": "anthropic"}
        except Exception as e:
            logger.warning(f"Anthropic chat failed: {e}")
            return {"content": f"Anthropic error: {e}", "tokens_used": 0, "mode": "error", "provider": "anthropic"}

    async def stream_chat(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.api_key)
            async with client.messages.stream(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.5),
                messages=[m for m in messages if m["role"] != "system"],
                system=next((m["content"] for m in messages if m["role"] == "system"), None),
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"[Anthropic error: {e}]"

    def get_info(self) -> dict:
        return {"provider": "anthropic", "model": self.model, "configured": bool(self.api_key)}


class OpenAIProvider:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.api_key = config.api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = config.model or "gpt-4o"

    async def chat(self, messages: list[dict], **kwargs) -> dict:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            resp = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.5),
            )
            return {"content": resp.choices[0].message.content or "", "tokens_used": resp.usage.total_tokens if resp.usage else 0, "mode": "openai", "provider": "openai"}
        except Exception as e:
            logger.warning(f"OpenAI chat failed: {e}")
            return {"content": f"OpenAI error: {e}", "tokens_used": 0, "mode": "error", "provider": "openai"}

    async def stream_chat(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)
            stream = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.5),
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"[OpenAI error: {e}]"

    def get_info(self) -> dict:
        return {"provider": "openai", "model": self.model, "configured": bool(self.api_key)}


class GeminiProvider:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.api_key = config.api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = config.model or "gemini-2.0-flash"

    async def chat(self, messages: list[dict], **kwargs) -> dict:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            prompt = "\n".join(m.get("content", "") for m in messages if m.get("content"))
            resp = await model.generate_content_async(prompt)
            return {"content": resp.text, "tokens_used": 0, "mode": "gemini", "provider": "gemini"}
        except Exception as e:
            logger.warning(f"Gemini chat failed: {e}")
            return {"content": f"Gemini error: {e}", "tokens_used": 0, "mode": "error", "provider": "gemini"}

    async def stream_chat(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            prompt = "\n".join(m.get("content", "") for m in messages if m.get("content"))
            resp = await model.generate_content_async(prompt, stream=True)
            async for chunk in resp:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"[Gemini error: {e}]"

    def get_info(self) -> dict:
        return {"provider": "gemini", "model": self.model, "configured": bool(self.api_key)}


class DeepSeekProvider:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.api_key = config.deepseek_api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.model = config.deepseek_model or "deepseek-chat"

    async def chat(self, messages: list[dict], **kwargs) -> dict:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key, base_url="https://api.deepseek.com/v1")
            resp = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.5),
            )
            return {"content": resp.choices[0].message.content or "", "tokens_used": resp.usage.total_tokens if resp.usage else 0, "mode": "deepseek", "provider": "deepseek"}
        except Exception as e:
            logger.warning(f"DeepSeek chat failed: {e}")
            return {"content": f"DeepSeek error: {e}", "tokens_used": 0, "mode": "error", "provider": "deepseek"}

    async def stream_chat(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key, base_url="https://api.deepseek.com/v1")
            stream = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 4096),
                temperature=kwargs.get("temperature", 0.5),
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"[DeepSeek error: {e}]"

    def get_info(self) -> dict:
        return {"provider": "deepseek", "model": self.model, "configured": bool(self.api_key)}


class LocalProvider:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.model = config.ollama_model or "llama3.2:1b"
        self.host = config.ollama_host or "http://127.0.0.1:11434"

    async def chat(self, messages: list[dict], **kwargs) -> dict:
        try:
            import httpx
            prompt = "\n".join(m.get("content", "") for m in messages if m.get("content"))
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{self.host}/api/generate", json={
                    "model": self.model, "prompt": prompt,
                    "max_tokens": kwargs.get("max_tokens", 4096),
                    "temperature": kwargs.get("temperature", 0.5),
                    "stream": False,
                })
                data = resp.json()
                return {"content": data.get("response", ""), "tokens_used": data.get("eval_count", 0), "mode": "local", "provider": "ollama"}
        except Exception as e:
            logger.warning(f"Local chat failed: {e}")
            return {"content": f"Local LLM error: {e}", "tokens_used": 0, "mode": "error", "provider": "local"}

    async def stream_chat(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        try:
            import httpx
            prompt = "\n".join(m.get("content", "") for m in messages if m.get("content"))
            async with httpx.AsyncClient(timeout=120) as client:
                async with client.stream("POST", f"{self.host}/api/generate", json={
                    "model": self.model, "prompt": prompt,
                    "max_tokens": kwargs.get("max_tokens", 4096),
                    "temperature": kwargs.get("temperature", 0.5),
                    "stream": True,
                }) as resp:
                    async for line in resp.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                text = data.get("response", "")
                                if text:
                                    yield text
                            except json.JSONDecodeError:
                                pass
        except Exception as e:
            yield f"[Local error: {e}]"

    def get_info(self) -> dict:
        return {"provider": "local", "model": self.model, "host": self.host}


class ModelProvider:
    def __init__(self, config: ModelConfig, engine=None):
        self.config = config
        if engine:
            self.engine = engine
        else:
            provider_type = config.provider or "local"
            if provider_type == "anthropic":
                self.engine = AnthropicProvider(config)
            elif provider_type == "openai":
                self.engine = OpenAIProvider(config)
            elif provider_type == "gemini":
                self.engine = GeminiProvider(config)
            elif provider_type == "deepseek":
                self.engine = DeepSeekProvider(config)
            else:
                self.engine = LocalProvider(config)

    async def chat(self, messages: list[dict], **kwargs) -> dict:
        return await self.engine.chat(messages, **kwargs)

    async def stream_chat(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        async for chunk in self.engine.stream_chat(messages, **kwargs):
            yield chunk

    def get_info(self) -> dict:
        return self.engine.get_info()


def create_provider(config: ModelConfig) -> ModelProvider:
    return ModelProvider(config)
