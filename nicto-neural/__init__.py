"""
NICTO Neural Core V1
Version: 1.0.0
Architecture: Transformer + MoE + 6-Brain System + PPO RL
Parameters: 284B+ (MoE declared)
Creator: Stephen Wahogo — Nairobi, Kenya
"""

from .neural_core import NeuralCore
from .neural.config import NeuralConfig
from .brain.consciousness import NeuralConsciousness
from .memory.manager import MemoryManager
from .neural.elo_system import EloSystem
from .learning.rl_agent import PPOAgent
from .learning.curriculum import CurriculumScheduler
from .reasoning.brainboost import BrainBoost
from .reasoning.consistency import ConsistencyTracker
from .learning.reward_shaper import RewardShaper
from .safety.reward_hacking import RewardHackingDetector
from .perception.feature_engine import TaskFeatureEngine
from .perception.normalizer import FeatureNormalizer
from .neural.model_selector import ModelSelector
from .neural.exploration import ExplorationManager
from .evolution.validation import ValidationEngine

__version__ = "1.0.0"
__all__ = [
    "NeuralCore", "NeuralConfig", "NeuralConsciousness",
    "MemoryManager", "EloSystem", "PPOAgent",
    "CurriculumScheduler", "BrainBoost", "ConsistencyTracker",
    "RewardShaper", "RewardHackingDetector",
    "TaskFeatureEngine", "FeatureNormalizer",
    "ModelSelector", "ExplorationManager", "ValidationEngine",
]
