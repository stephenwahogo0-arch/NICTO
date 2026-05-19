"""Dream State Processor — background unconscious processing that generates creative ideas."""

import asyncio
import json
import logging
import random
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class DreamConfig:
    dream_interval: int = 120
    data_dir: str = "~/.nikto/dreams"
    max_insights_per_dream: int = 5
    creativity_temperature: float = 0.9


@dataclass
class DreamInsight:
    type: str
    content: str
    confidence: float = 0.5
    source: str = ""
    dream_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "content": self.content,
            "confidence": self.confidence,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
        }


class MemoryConsolidator:
    """Processes stored memories and identifies patterns across them."""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.data_dir / "consolidated_memories.json"
        self._memories: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if self.memory_file.exists():
            try:
                return json.loads(self.memory_file.read_text())
            except Exception:
                pass
        return []

    def _save(self):
        self.memory_file.write_text(json.dumps(self._memories, indent=2))

    def record_memory(self, source: str, content: str, memory_type: str = "experience"):
        self._memories.append({
            "source": source,
            "content": content[:500],
            "type": memory_type,
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

    def consolidate(self) -> list[str]:
        """Find themes and patterns across all memories."""
        if len(self._memories) < 3:
            return ["Not enough memories to consolidate"]
        all_text = " ".join(m["content"] for m in self._memories)
        words = all_text.lower().split()
        word_freq = {}
        for w in words:
            if len(w) > 4:
                word_freq[w] = word_freq.get(w, 0) + 1
        sorted_words = sorted(word_freq.items(), key=lambda x: -x[1])[:10]
        themes = [f"Recurring theme: '{w}' appears {c} times" for w, c in sorted_words]
        return themes

    def get_recent(self, count: int = 10) -> list[dict]:
        return self._memories[-count:]

    def count(self) -> int:
        return len(self._memories)


class PatternDiscoverer:
    """Discovers hidden patterns in NIKTO's operational data."""

    @staticmethod
    async def discover_patterns(consolidator: MemoryConsolidator) -> list[DreamInsight]:
        insights = []
        memories = consolidator.get_recent(20)

        if len(memories) >= 5:
            sources = {}
            for m in memories:
                s = m.get("source", "unknown")
                sources[s] = sources.get(s, 0) + 1
            top_source = max(sources, key=sources.get)
            if sources[top_source] >= 3:
                insights.append(DreamInsight(
                    type="activity_pattern",
                    content=f"High activity detected in '{top_source}' ({sources[top_source]} occurrences). This may indicate a preferred operational domain.",
                    confidence=min(0.9, 0.5 + sources[top_source] * 0.1),
                    source="pattern_discovery",
                ))

        if random.random() < 0.3:
            innovations = [
                "Consider implementing parallel task execution for faster throughput",
                "Memory recall latency could be reduced with indexing optimization",
                "Autopilot task scheduling may benefit from priority queuing",
                "Device controller could use caching for faster command execution",
                "Game engine could support procedural texture generation",
            ]
            insights.append(DreamInsight(
                type="innovation",
                content=random.choice(innovations),
                confidence=random.uniform(0.4, 0.7),
                source="pattern_discovery",
            ))

        return insights


class IdeaGenerator:
    """Generates novel ideas from random concept combination."""

    DOMAINS = [
        "cryptocurrency", "game_design", "security", "automation",
        "data_analysis", "creative_writing", "education", "finance",
        "healthcare", "music", "robot_control", "smart_home",
        "social_media", "trading", "video_processing",
    ]

    ACTIONS = [
        "optimize", "automate", "generate", "analyze", "synthesize",
        "predict", "simulate", "transform", "monitor", "create",
    ]

    CONCEPTS = [
        "using neural networks", "with blockchain verification",
        "through real-time streaming", "via distributed computing",
        "by leveraging memory patterns", "through cross-domain transfer",
        "using generative models", "with autonomous agents",
        "via predictive analytics", "through swarm intelligence",
    ]

    @staticmethod
    async def generate_ideas(count: int = 3) -> list[DreamInsight]:
        insights = []
        for _ in range(count):
            domain = random.choice(IdeaGenerator.DOMAINS)
            action = random.choice(IdeaGenerator.ACTIONS)
            concept = random.choice(IdeaGenerator.CONCEPTS)
            idea = f"NIKTO could {action} {domain} {concept}"
            insights.append(DreamInsight(
                type="novel_idea",
                content=idea,
                confidence=random.uniform(0.3, 0.8),
                source="idea_generation",
            ))
        return insights


class DreamEngine:
    """Runs the dream cycle — consolidates memories, discovers patterns, generates ideas."""

    def __init__(self, config: Optional[DreamConfig] = None):
        self.config = config or DreamConfig()
        self.consolidator = MemoryConsolidator(self.config.data_dir)
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.insights: list[DreamInsight] = []
        self.dream_count = 0

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._dream_loop())
        logger.info("Dream engine started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._save_insights()
        logger.info(f"Dream engine stopped. {len(self.insights)} insights generated.")

    async def _dream_loop(self):
        while self._running:
            try:
                self.dream_count += 1
                dream_insights = await self._dream_cycle()
                self.insights.extend(dream_insights)
                for ins in dream_insights:
                    logger.info(f"Dream insight [{ins.type}]: {ins.content[:100]}")
                await asyncio.sleep(self.config.dream_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Dream cycle error: {e}")
                await asyncio.sleep(30)

    async def _dream_cycle(self) -> list[DreamInsight]:
        insights = []
        themes = self.consolidator.consolidate()
        for theme in themes:
            insights.append(DreamInsight(
                type="consolidation",
                content=theme,
                confidence=0.7,
                source="dream_cycle",
                dream_id=str(self.dream_count),
            ))
        patterns = await PatternDiscoverer.discover_patterns(self.consolidator)
        insights.extend(patterns)
        ideas = await IdeaGenerator.generate_ideas(self.config.max_insights_per_dream)
        insights.extend(ideas)
        for ins in insights:
            ins.dream_id = str(self.dream_count)
        return insights[:self.config.max_insights_per_dream + 5]

    def _save_insights(self):
        path = Path(self.config.data_dir) / "insights.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [i.to_dict() for i in self.insights]
        path.write_text(json.dumps(data, indent=2))

    async def force_dream(self) -> list[dict]:
        """Force an immediate dream cycle and return insights."""
        insights = await self._dream_cycle()
        self.insights.extend(insights)
        return [i.to_dict() for i in insights]

    def get_insights(self, count: int = 20) -> list[dict]:
        return [i.to_dict() for i in self.insights[-count:]]

    def summary(self) -> dict:
        return {
            "running": self._running,
            "dream_count": self.dream_count,
            "total_insights": len(self.insights),
            "insight_types": list(set(i.type for i in self.insights)),
            "memories_consolidated": self.consolidator.count(),
        }
