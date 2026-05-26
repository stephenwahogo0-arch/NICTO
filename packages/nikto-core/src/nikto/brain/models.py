"""
Nikto Brain Data Models.

All dataclasses, enums, and type definitions used by NICTO's brain modules.
These are the building blocks of NICTO's cognitive architecture.
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional
from uuid import uuid4


class Intent(Enum):
    """
    Classification of user intent based on message analysis.
    NICTO uses intent classification to determine how to approach
    any incoming request.
    """
    BUILD = "build"       # User wants to create something
    LEARN = "learn"       # User wants to understand something
    DEBUG = "debug"       # User has a problem to fix
    ATTACK = "attack"    # Security testing request
    ANALYZE = "analyze"  # User wants analysis of something
    GENERATE = "generate"  # User wants content created
    QUESTION = "question"  # Factual question
    INSTRUCT = "instruct"  # User is giving NICTO a command
    CONVERSE = "converse"  # Casual conversation
    EMOTIONAL = "emotional"  # User needs emotional support


class EmotionalStateEnum(Enum):
    """
    Detected emotional states that NICTO can respond to.
    """
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    EXCITED = "excited"
    CONFUSED = "confused"
    URGENT = "urgent"
    HOSTILE = "hostile"
    CURIOUS = "curious"
    SAD = "sad"


@dataclass
class Perception:
    """
    Structured understanding of raw user input.
    
    When NICTO receives any input, it breaks it down into
    structured components: what the user wants, what they
    need, and what emotional state they're in.
    """
    raw_input: str
    intent: Intent
    entities: list[str]
    sentiment: str
    domain: str
    expertise_required: str
    language: str
    context: dict
    id: str = field(default_factory=lambda: str(uuid4())[:12])
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ReasoningResult:
    """
    Result from a single reasoning strategy.
    
    Each of NICTO's 5 reasoning strategies produces a result
    with conclusions and a confidence score.
    """
    strategy: str
    conclusions: list[str]
    confidence: float


@dataclass
class SynthesisResult:
    """
    Combined output from all reasoning strategies.
    
    NICTO runs 5 reasoning strategies in parallel and synthesizes
    them into one best answer with alternatives.
    """
    best_answer: str
    alternatives: list[str]
    gaps: list[str]


@dataclass
class Reasoning:
    """
    Full reasoning output with chain of thought.
    
    Contains the conclusion, confidence level, step-by-step
    reasoning chain, and any knowledge gaps identified.
    """
    conclusion: str
    confidence: float
    chain: list[str]
    alternatives: list[str]
    knowledge_gaps: list[str]
    requires_clarification: bool
    domain: str = ""

    def add_uncertainty_qualifier(self) -> None:
        """
        Add uncertainty qualifier when confidence is low.
        Modifies the conclusion to indicate lower confidence.
        """
        self.conclusion = (
            f"Based on available knowledge "
            f"(confidence: {self.confidence:.0%}): "
            f"{self.conclusion}"
        )


@dataclass
class NiktoThought:
    """
    The final thought output from NICTO's brain.
    
    After the full thinking pipeline, NICTO produces a thought
    containing the response, confidence, and metadata about
    how it arrived at the answer.
    """
    response: str
    confidence: float
    reasoning_chain: list[str]
    knowledge_used: list[str]
    memory_updated: bool


@dataclass
class JudgmentResult:
    """
    Result from NICTO's conscience evaluating a response.
    
    Determines if a response is approved or if it violates
    NICTO's ethical principles.
    """
    approved: bool
    reason: str
    alternative: Optional[str] = None


@dataclass
class HarmCheck:
    """
    Result from checking if a response could cause harm.
    
    NICTO distinguishes between educational security content
    (allowed) and targeted attack assistance (not allowed).
    """
    is_harmful: bool
    reason: str
    alternative: str = ""


@dataclass
class EmotionalState:
    """
    Detected emotional state and how to adjust response.
    
    NICTO detects user emotions and adjusts communication
    style accordingly — more patience for frustrated users,
    more energy for excited users, etc.
    """
    state: str
    adjustment: dict


@dataclass
class Memory:
    """
    A stored memory with relevance scoring.
    
    Memories are retrieved based on relevance to current
    context and ranked by both relevance and recency.
    """
    id: str
    content: str
    domain: str
    timestamp: datetime
    relevance_score: float = 0.0


@dataclass
class MemoryEvent:
    """
    A single event to be stored in memory.
    
    After each interaction, NICTO stores the event across
    all three memory types: episodic, semantic, and procedural.
    """
    input: str
    response: str
    domain: str
    complexity: float
    user_id: Optional[str]
    languages_mentioned: list[str] = field(default_factory=list)
    project_references: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserModel:
    """
    NICTO's model of a specific user.
    
    Tracks expertise level, communication preferences,
    active projects, and behavioral patterns over time.
    """
    user_id: str
    expertise: dict = field(default_factory=dict)
    language_preferences: list[str] = field(default_factory=list)
    active_projects: list[str] = field(default_factory=list)
    interaction_count: int = 0
    last_seen: Optional[datetime] = None

    def update_expertise(self, domain: str, level: float) -> None:
        """Update expertise level using rolling average."""
        if domain not in self.expertise:
            self.expertise[domain] = level
        else:
            # Rolling average - 80% old, 20% new
            self.expertise[domain] = (
                self.expertise[domain] * 0.8 + level * 0.2
            )

    def note_language_preference(self, languages: list[str]) -> None:
        """Track user's language preferences."""
        for lang in languages:
            if lang not in self.language_preferences:
                self.language_preferences.append(lang)

    def update_projects(self, projects: list[str]) -> None:
        """Track user's active projects."""
        for project in projects:
            if project not in self.active_projects:
                self.active_projects.append(project)


@dataclass
class KnowledgeFact:
    """
    A single piece of factual knowledge in NICTO's knowledge base.
    """
    id: str
    content: str
    domain: str
    confidence: float
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgeSet:
    """
    Collection of knowledge retrieved for a given query.
    
    Includes coverage score indicating how well NICTO's
    knowledge covers the topic.
    """
    items: list[KnowledgeFact]
    domain: str
    coverage_score: float
    gaps: list[str]


@dataclass
class LearningResult:
    """
    Result from NICTO learning from an interaction.
    
    Indicates quality score, whether new knowledge was gained,
    and whether an improvement task was queued.
    """
    quality_score: float
    learned_something_new: bool
    improvement_queued: bool


@dataclass
class Goal:
    """
    A persistent goal NICTO works toward.
    
    Goals have metrics and targets measured over time periods.
    NICTO tracks progress on all permanent goals.
    """
    id: str
    description: str
    metric: str
    target: float
    per: str


@dataclass
class GoalProgress:
    """
    Progress on a single goal.
    
    Shows current value and whether NICTO is on track.
    """
    goal: Goal
    current_value: float
    on_track: bool


@dataclass
class GoalReport:
    """
    Full report on all goals and their progress.
    """
    goals: list[GoalProgress]


@dataclass
class ImprovementTask:
    """
    A self-improvement task queued after a low-quality interaction.
    """
    topic: str
    gap_description: str
    priority: float
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ErrorPattern:
    """
    A recurring error pattern NICTO has identified in itself.
    """
    pattern_id: str
    description: str
    frequency: int
    last_seen: datetime
    example_inputs: list[str] = field(default_factory=list)


@dataclass
class PerformanceRecord:
    """
    Record of a single interaction's performance.
    """
    input: str
    response: str
    confidence: float
    quality: float
    reasoning_chain: list[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)