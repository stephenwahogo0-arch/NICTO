import uuid
import json
import hashlib
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime, timezone


class ThinkingStyle(Enum):
    DEDUCTIVE = "deductive"
    INDUCTIVE = "inductive"
    ABDUCTIVE = "abductive"
    ANALOGICAL = "analogical"
    CRITICAL = "critical"
    CREATIVE = "creative"
    INTUITIVE = "intuitive"
    ANALYTICAL = "analytical"


class EmotionType(Enum):
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    FEAR = "fear"
    SURPRISE = "surprise"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    CURIOSITY = "curiosity"
    CONFUSION = "confusion"
    NEUTRAL = "neutral"


class KnowledgeLevel(Enum):
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"


class GoalStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    BLOCKED = "blocked"


@dataclass
class Thought:
    content: str
    style: ThinkingStyle = ThinkingStyle.ANALYTICAL
    confidence: float = 0.5
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    id: str = field(default_factory=lambda: hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16])
    parent_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["style"] = self.style.value
        return d

    def __post_init__(self):
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass
class MemoryFragment:
    content: str
    tags: list = field(default_factory=list)
    importance: float = 0.5
    emotional_valence: float = 0.0
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    access_count: int = 0
    strength: float = 1.0
    id: str = field(default_factory=lambda: hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16])
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def access(self):
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc).isoformat()

    def decay(self, rate: float = 0.01):
        self.strength = max(0.0, self.strength - rate * (1.0 - self.importance))

    def reinforce(self, amount: float = 0.1):
        self.strength = min(1.0, self.strength + amount)

    def __post_init__(self):
        self.importance = max(0.0, min(1.0, self.importance))
        self.strength = max(0.0, min(1.0, self.strength))
        self.emotional_valence = max(-1.0, min(1.0, self.emotional_valence))


@dataclass
class Belief:
    statement: str
    confidence: float = 0.5
    source: str = "direct_experience"
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence_for: list = field(default_factory=list)
    evidence_against: list = field(default_factory=list)
    id: str = field(default_factory=lambda: hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16])

    def to_dict(self) -> dict:
        return asdict(self)

    def update_confidence(self) -> float:
        total = len(self.evidence_for) + len(self.evidence_against)
        if total == 0:
            return self.confidence
        ratio = len(self.evidence_for) / total
        self.confidence = 0.3 + 0.7 * ratio
        self.updated = datetime.now(timezone.utc).isoformat()
        return self.confidence

    def __post_init__(self):
        self.confidence = max(0.0, min(1.0, self.confidence))


@dataclass
class Goal:
    description: str
    priority: int = 5
    status: GoalStatus = GoalStatus.ACTIVE
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    deadline: Optional[str] = None
    subgoals: list = field(default_factory=list)
    progress: float = 0.0
    id: str = field(default_factory=lambda: hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16])
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    def update_progress(self, amount: float):
        self.progress = max(0.0, min(1.0, self.progress + amount))
        if self.progress >= 1.0:
            self.status = GoalStatus.COMPLETED


@dataclass
class EmotionalState:
    primary_emotion: EmotionType = EmotionType.NEUTRAL
    intensity: float = 0.0
    valence: float = 0.0
    arousal: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    history: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["primary_emotion"] = self.primary_emotion.value
        return d


@dataclass
class MoralRule:
    principle: str
    weight: float = 1.0
    category: str = "ethical"
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    id: str = field(default_factory=lambda: hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16])

    def to_dict(self) -> dict:
        return asdict(self)
