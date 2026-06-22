"""NICTO X — Frontier AI Architecture with neural core, multi-agent systems, memory, reasoning, and autonomous execution."""

from nicto_x.core.config import NictoXConfig
from nicto_x.core.orchestrator import NictoXOrchestrator
from nicto_x.agents.bus import AgentBus
from nicto_x.memory.consolidation import MemoryConsolidator
from nicto_x.neural.core import NeuralCore, MoEConfig, AttentionConfig
from nicto_x.neural.tokenizer import NeuralTokenizer
from nicto_x.knowledge.graph import KnowledgeGraph
from nicto_x.knowledge.vector_store import VectorStore
from nicto_x.software.engineer import SoftwareEngineer
from nicto_x.research.literature import LiteratureReview
from nicto_x.vision.analyzer import VisionAnalyzer
from nicto_x.security.auth import AuthManager
from nicto_x.self_improvement.benchmark import BenchmarkRunner
from nicto_x.distributed.executor import DistributedExecutor, WorkQueue

__version__ = "0.2.0"

__all__ = [
    "NictoXConfig",
    "NictoXOrchestrator",
    "AgentBus",
    "MemoryConsolidator",
    "NeuralCore",
    "MoEConfig",
    "AttentionConfig",
    "NeuralTokenizer",
    "KnowledgeGraph",
    "VectorStore",
    "SoftwareEngineer",
    "LiteratureReview",
    "VisionAnalyzer",
    "AuthManager",
    "BenchmarkRunner",
    "DistributedExecutor",
    "WorkQueue",
]
