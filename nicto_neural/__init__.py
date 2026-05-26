from .neural_core import NeuralCore
from .neural.config import NeuralConfig
from .neural.elo_system import ELOEstimator
from .neural.exploration import ExplorationEngine
from .neural.domain_profiler import DomainProfiler
from .perception.tokenizer import Tokenizer
from .perception.feature_engine import FeatureEngine
from .memory.manager import MemoryManager
from .memory.cross_session import CrossSessionMemory
from .memory.context_compressor import ContextCompressor
from .brain.consciousness import NeuralConsciousness
from .reasoning.multi_path_cot import MultiPathCoT, ReasoningPath, MultiPathResult
from .reasoning.calibration_engine import CalibrationEngine
from .reasoning.pattern_discovery import PatternDiscoveryEngine
from .reasoning.hallucination_eliminator import HallucinationEliminator, EliminationResult
from .reasoning.reflection import ReflectionEngine
from .reasoning.consistency import ConsistencyTracker
from .learning.realtime_improvement import RealtimeImprovementEngine, ImprovementResult
from .learning.meta_learner import MetaLearner
from .learning.reward_model import RewardModel
from .metrics.super_benchmark import SuperBenchmark

# Real AI Module Imports
from .run_nicto import NICTOInference
from .nicto_image_gen import NICTOImageGen
from .nicto_video_gen import NICTOVideoGen
from .nicto_game_builder import NICTOGameBuilder
from .setup_real_ai import run as setup_real_ai
from .train_nicto import main as train_nicto
from .build_training_data import main as build_training_data
from .nicto_master import main as nicto_master

__version__ = "2.1.0"
__codename__ = "REAL_AI"

__all__ = [
    "NeuralCore",
    "NeuralConfig",
    "ELOEstimator",
    "ExplorationEngine",
    "DomainProfiler",
    "Tokenizer",
    "FeatureEngine",
    "MemoryManager",
    "CrossSessionMemory",
    "ContextCompressor",
    "NeuralConsciousness",
    "MultiPathCoT",
    "ReasoningPath",
    "MultiPathResult",
    "CalibrationEngine",
    "PatternDiscoveryEngine",
    "HallucinationEliminator",
    "EliminationResult",
    "ReflectionEngine",
    "ConsistencyTracker",
    "RealtimeImprovementEngine",
    "ImprovementResult",
    "MetaLearner",
    "RewardModel",
    "SuperBenchmark",
    # Real AI Modules
    "NICTOInference",
    "NICTOImageGen",
    "NICTOVideoGen",
    "NICTOGameBuilder",
    "setup_real_ai",
    "train_nicto",
    "build_training_data",
    "nicto_master",
]
