"""NICTO X — Configuration system."""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ModelConfig:
    provider: str = "auto"
    model_id: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.95
    use_gpu: bool = True


@dataclass
class AgentConfig:
    max_concurrent: int = 4
    timeout_seconds: int = 120
    retry_attempts: int = 3


@dataclass
class MemoryConfig:
    episodic_capacity: int = 10000
    semantic_capacity: int = 50000
    working_memory_size: int = 50
    consolidation_interval: int = 300
    vector_dim: int = 768
    relevance_top_k: int = 10


@dataclass
class KnowledgeConfig:
    graph_store_path: str = ""
    vector_store_path: str = ""
    embedding_model: str = "all-MiniLM-L6-v2"
    max_documents: int = 1_000_000


@dataclass
class SecurityConfig:
    auth_enabled: bool = True
    token_expiry_hours: int = 24
    encryption_key: str = ""
    audit_log_path: str = ""


@dataclass
class NictoXConfig:
    model: ModelConfig = field(default_factory=ModelConfig)
    agents: AgentConfig = field(default_factory=AgentConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    knowledge: KnowledgeConfig = field(default_factory=KnowledgeConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    data_dir: str = field(default_factory=lambda: str(
        Path.home() / ".nicto-x"
    ))
    log_level: str = "INFO"
    version: str = "0.1.0"

    def __post_init__(self):
        if not self.knowledge.graph_store_path:
            self.knowledge.graph_store_path = os.path.join(
                self.data_dir, "knowledge_graph.json"
            )
        if not self.knowledge.vector_store_path:
            self.knowledge.vector_store_path = os.path.join(
                self.data_dir, "vectors"
            )
        if not self.security.audit_log_path:
            self.security.audit_log_path = os.path.join(
                self.data_dir, "audit.log"
            )

    @classmethod
    def from_file(cls, path: str) -> "NictoXConfig":
        with open(path) as f:
            data = json.load(f)
        return cls(**data)

    def save(self, path: Optional[str] = None) -> str:
        path = path or os.path.join(self.data_dir, "config.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.__dict__, f, indent=2, default=str)
        return path
