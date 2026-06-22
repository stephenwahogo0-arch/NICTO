from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, ClassVar
from enum import Enum


class AgentMode(str, Enum):
    PLAN = "plan"
    BUILD = "build"
    AUTONOMOUS = "autonomous"
    INTERACTIVE = "interactive"
    DAEMON = "daemon"


class ModelConfig(BaseModel):
    provider: str = "local"
    model: str = "local"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.4
    max_tokens: int = 4096
    thinking_mode: bool = False
    ollama_model: str = "llama3.2:1b"
    ollama_host: str = "http://127.0.0.1:11434"
    model_path: Optional[str] = None
    n_gpu_layers: Optional[int] = None
    model_tier: str = "auto"
    language: str = "auto"
    deepseek_api_key: Optional[str] = None
    deepseek_model: str = "deepseek-chat"


class MemoryConfig(BaseModel):
    vector_store: str = "chroma"
    max_context_chunks: int = 5
    embedding_model: str = "all-MiniLM-L6-v2"


class KnowledgeConfig(BaseModel):
    max_results: int = 10
    min_confidence: float = 0.5
    use_chroma: bool = True


class SecurityConfig(BaseModel):
    sandbox_enabled: bool = True
    code_scan: bool = True
    allow_network: bool = False
    max_file_size_mb: int = 10


class AgentConfig(BaseModel):
    data_dir: str = "~/.nikto"
    model: ModelConfig = Field(default_factory=ModelConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    knowledge: KnowledgeConfig = Field(default_factory=KnowledgeConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    mode: AgentMode = AgentMode.INTERACTIVE
    system_prompt: str = "You are NIKTO, a highly capable AI assistant."
    max_tokens: int = 4096
    temperature: float = 0.5


class DaemonConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 4890
    workers: int = 4
    log_level: str = "info"


class NiktoConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NIKTO_", env_nested_delimiter="__", extra="allow")

    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None

    model: ModelConfig = Field(default_factory=ModelConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    daemon: DaemonConfig = Field(default_factory=DaemonConfig)