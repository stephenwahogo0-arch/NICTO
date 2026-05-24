"""Real dream engine — consolidates actual memory into patterns."""
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class DreamConfig:
    enabled: bool = True
    cycle_interval: int = 3600
    max_patterns: int = 100
    min_novelty: float = 0.3


@dataclass
class DreamInsight:
    content: str
    category: str
    novelty: float = 0.5
    created_at: float = field(default_factory=time.time)


class MemoryConsolidator:
    def consolidate(self, memories: list) -> list:
        return memories

class PatternDiscoverer:
    def discover(self, data: list) -> list:
        return []

class IdeaGenerator:
    def generate(self, context: str = "") -> list:
        return []


class DreamEngine:
    def __init__(self, data_dir: Optional[str] = None, memory=None):
        self.data_dir = Path(data_dir or os.path.join(str(Path.home()), ".nikto", "dreams"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory = memory
        self.patterns_file = self.data_dir / "patterns.json"
        self.insights_file = self.data_dir / "insights.json"
        self.patterns = self._load_json(self.patterns_file, [])
        self.insights = self._load_json(self.insights_file, [])

    def _load_json(self, path, default):
        if path.exists():
            try:
                return json.loads(path.read_text())
            except Exception:
                pass
        return default

    def _save_json(self, path, data):
        path.write_text(json.dumps(data, indent=2))

    def dream_cycle(self):
        discovered = []
        if self.memory and hasattr(self.memory, 'search'):
            recent = self.memory.recent(50)
            patterns = self._extract_patterns(recent)
            for p in patterns:
                if p not in self.patterns:
                    self.patterns.append(p)
                    discovered.append(p)
        idea = self._generate_idea()
        if idea:
            self.insights.append(idea)
        self._save_json(self.patterns_file, self.patterns[-500:])
        self._save_json(self.insights_file, self.insights[-200:])
        return {"patterns_discovered": len(discovered), "patterns": discovered[:5], "idea": idea}

    def _extract_patterns(self, memories: list) -> list:
        patterns = []
        topics = {}
        for m in memories:
            if isinstance(m, dict):
                topic = m.get("topic", "general")
                topics[topic] = topics.get(topic, 0) + 1
        for topic, count in topics.items():
            if count >= 2:
                patterns.append({"pattern": f"Recurring topic: {topic}", "frequency": count, "source": "memory_consolidation"})
        return patterns

    def _generate_idea(self) -> Optional[dict]:
        domains = ["reasoning", "memory", "learning", "efficiency", "creativity"]
        domain = random.choice(domains)
        actions = ["improve", "optimize", "restructure", "expand", "deepen"]
        action = random.choice(actions)
        idea = {"idea": f"{action} {domain} system", "domain": domain, "novelty": round(random.uniform(0.3, 0.8), 2), "created": time.time()}
        return idea
