"""Brain Engine — NICTO's Cognitive Architecture.

This module contains NICTO's core brain system which includes:
- NiktoBrain: The central intelligence that orchestrates all components
- NiktoIdentity: NICTO's permanent, immutable identity
- NiktoReasoner: Multi-strategy reasoning engine
- NiktoLongTermMemory: Persistent memory across sessions
- NiktoLearner: Self-improvement engine
- NiktoKnowledgeCore: Internal knowledge base
- NiktoEmotionalCore: Emotional intelligence layer
- NiktoConscience: Ethical judgment system
- NiktoLanguageEngine: Response generation in NICTO's voice
- NiktoGoalSystem: Persistent goal management
"""

# Keep existing exports for backward compatibility
from .engine import BrainEngine
from .multiprocess import MultiprocessBrain, ParallelRegion

# Export new brain modules
from .models import (
    Intent,
    Perception,
    Reasoning,
    ReasoningResult,
    SynthesisResult,
    NiktoThought,
    JudgmentResult,
    HarmCheck,
    EmotionalState,
    Memory,
    MemoryEvent,
    UserModel,
    KnowledgeFact,
    KnowledgeSet,
    LearningResult,
    Goal,
    GoalProgress,
    GoalReport,
    ImprovementTask,
    ErrorPattern,
    PerformanceRecord,
)

from .identity import NiktoIdentity
from .reasoner import NiktoReasoner
from .memory import NiktoLongTermMemory, UserModelStore
from .learner import NiktoLearner, PerformanceLog
from .knowledge import NiktoKnowledgeCore
from .emotion import NiktoEmotionalCore
from .conscience import NiktoConscience
from .language import NiktoLanguageEngine
from .goals import NiktoGoalSystem
from .core import NiktoBrain

__all__ = [
    # Existing exports
    "BrainEngine",
    "MultiprocessBrain",
    "ParallelRegion",
    # Models
    "Intent",
    "Perception",
    "Reasoning",
    "ReasoningResult",
    "SynthesisResult",
    "NiktoThought",
    "JudgmentResult",
    "HarmCheck",
    "EmotionalState",
    "Memory",
    "MemoryEvent",
    "UserModel",
    "KnowledgeFact",
    "KnowledgeSet",
    "LearningResult",
    "Goal",
    "GoalProgress",
    "GoalReport",
    "ImprovementTask",
    "ErrorPattern",
    "PerformanceRecord",
    # Brain components
    "NiktoBrain",
    "NiktoIdentity",
    "NiktoReasoner",
    "NiktoLongTermMemory",
    "NiktoLearner",
    "NiktoKnowledgeCore",
    "NiktoEmotionalCore",
    "NiktoConscience",
    "NiktoLanguageEngine",
    "NiktoGoalSystem",
    "UserModelStore",
    "PerformanceLog",
]
