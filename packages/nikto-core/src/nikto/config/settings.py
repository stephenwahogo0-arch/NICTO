"""NIKTO configuration — with real LLM engine settings."""
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    provider: str = "local"
    model: str = "local"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.5
    max_tokens: int = 4096
    thinking_mode: bool = False
    
    # Ollama config
    ollama_model: str = "llama3.2:1b"
    ollama_host: str = "http://127.0.0.1:11434"
    
    # GGUF / llama.cpp config
    model_path: Optional[str] = None
    n_gpu_layers: Optional[int] = None
    model_tier: str = "auto"  # "tier1", "tier2", "auto"
    # Language config
    language: str = "auto"  # "auto" = detect from user input, or ISO code like "en", "es", "zh", etc.


class MemoryConfig(BaseModel):
    type: str = "hybrid"
    sqlite_path: str = "~/.nikto/memory.db"
    chroma_path: str = "~/.nikto/chroma_db"
    vector_dimension: int = 768


class KnowledgeConfig(BaseModel):
    enabled: bool = True
    auto_ingest: bool = True
    knowledge_path: str = "~/.nikto/knowledge_base.json"
    vector_path: str = "~/.nikto/chroma_kb"
    max_context_features: int = 50


class SecurityConfig(BaseModel):
    sandbox_enabled: bool = False
    sandbox_type: str = "docker"
    allowed_commands: list[str] = Field(default_factory=lambda: ["*"])
    allowed_paths: list[str] = Field(default_factory=lambda: ["*"])
    allow_bash: bool = True
    allow_network: bool = True


class CryptoConfig(BaseModel):
    enabled: bool = False
    wallet_name: str = "NiktoEarningVault"
    network: str = "bitcoin"
    target_address: Optional[str] = None
    auto_payout: bool = False
    auto_payout_threshold_btc: float = 0.001


class NiktoConfig(BaseModel):
    mode: str = "build"
    debug: bool = False
    verbose: bool = False
    workspace: str = "."
    data_dir: str = "~/.nikto"

    model: ModelConfig = Field(default_factory=ModelConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    crypto: CryptoConfig = Field(default_factory=CryptoConfig)

    plugins: list[str] = Field(default_factory=list)
    mcp_servers: list[dict] = Field(default_factory=list)
    skills_dirs: list[str] = Field(default_factory=list)

    @classmethod
    def load(cls, path: Optional[str] = None) -> "NiktoConfig":
        import json
        import yaml

        config_paths = [
            path,
            "nikto.json",
            "nikto.jsonc",
            "nikto.yaml",
            "nikto.yml",
            os.path.join(os.getcwd(), "nikto.json"),
            os.path.join(os.getcwd(), "nikto.yaml"),
        ]

        for cp in config_paths:
            if cp and os.path.exists(cp):
                with open(cp) as f:
                    if cp.endswith((".yaml", ".yml")):
                        data = yaml.safe_load(f)
                    else:
                        data = json.load(f)
                    return cls(**data)
        return cls()

    def save(self, path: str = "nikto.json"):
        import json
        with open(path, "w") as f:
            json.dump(self.model_dump(), f, indent=2)

    @property
    def data_dir_path(self) -> Path:
        p = Path(self.data_dir).expanduser()
        p.mkdir(parents=True, exist_ok=True)
        return p
