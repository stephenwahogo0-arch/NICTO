"""Memory manager — central coordinator for all memory stores."""

from pathlib import Path

from .base import MemoryEntry
from .consistency import ConsistencyMemory
from .episodic import EpisodicMemory
from .experience import ExperienceBuffer
from .goals import GoalMemory
from .performance import PerformanceMemory
from .personality import PersonalityMemory
from .reflection import ReflectionMemory
from .semantic import SemanticMemory
from .skills import SkillMemory
from .task_features import TaskFeatureMemory


class MemoryManager:
    """Central coordinator for all memory stores."""

    def __init__(self, config):
        db_base = Path(config.memory_db_path).expanduser()
        self.episodic = EpisodicMemory(db_base / "episodic")
        self.semantic = SemanticMemory(db_base / "semantic")
        self.skills = SkillMemory(db_base / "skills")
        self.goals = GoalMemory(db_base / "goals")
        self.personality = PersonalityMemory(db_base / "personality")
        self.reflection = ReflectionMemory(db_base / "reflection")
        self.performance = PerformanceMemory(db_base / "performance")
        self.task_features = TaskFeatureMemory(db_base / "task_features")
        self.consistency = ConsistencyMemory(db_base / "consistency")
        self.experience = ExperienceBuffer(config.experience_buffer_size)

    def store_episode(self, content, metadata=None) -> str:
        entry = MemoryEntry(content=content, metadata=metadata or {}, importance=0.5)
        return self.episodic.store(entry)

    def recall_recent(self, limit: int = 10) -> list:
        return self.episodic.recall("recent", limit)

    def add_experience(self, state, action, reward, next_state, done) -> None:
        self.experience.add(state, action, reward, next_state, done)

    def consolidate(self) -> None:
        """Move important short-term to long-term."""
        recent = self.episodic.recall("consolidate", 100)
        for entry in recent:
            if entry.importance > 0.8:
                self.semantic.store(MemoryEntry(
                    content=entry.content,
                    metadata={**entry.metadata, "consolidated": True},
                    importance=entry.importance,
                ))

    def total_memories(self) -> dict:
        return {
            "episodic": self.episodic.count(),
            "semantic": self.semantic.count(),
            "skills": self.skills.count(),
            "goals": self.goals.count(),
            "reflections": self.reflection.count(),
        }
