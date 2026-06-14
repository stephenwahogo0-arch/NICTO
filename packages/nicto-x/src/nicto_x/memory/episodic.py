"""NICTO X — Episodic memory: stores conversations, projects, tasks, and decisions."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from nicto_x.core.config import MemoryConfig

logger = logging.getLogger("nicto_x.memory.episodic")


@dataclass
class Episode:
    id: str = ""
    timestamp: float = field(default_factory=time.time)
    content: dict = field(default_factory=dict)
    importance: float = 0.5
    tags: list[str] = field(default_factory=list)
    embedding: Optional[list[float]] = None


class EpisodicMemory:
    """Stores experiences, conversations, and historical decisions."""

    def __init__(self, config: MemoryConfig):
        self.config = config
        self._episodes: list[Episode] = []
        self._index: dict[str, list[str]] = {}
        self._path = Path.home() / ".nicto-x" / "episodic.json"

    def __len__(self) -> int:
        return len(self._episodes)

    async def store(self, data: dict, tags: Optional[list[str]] = None) -> str:
        episode = Episode(
            id=f"ep_{int(time.time() * 1000)}_{len(self._episodes)}",
            content=data,
            importance=data.get("importance", 0.5),
            tags=tags or [],
        )
        self._episodes.append(episode)
        for tag in episode.tags:
            self._index.setdefault(tag, []).append(episode.id)
        if len(self._episodes) > self.config.episodic_capacity:
            self._episodes.sort(key=lambda e: e.importance)
            self._episodes = self._episodes[-self.config.episodic_capacity:]
        return episode.id

    async def search(
        self, query: str, top_k: int = 10
    ) -> list[dict]:
        query_lower = query.lower()
        scored = []
        for ep in self._episodes:
            score = 0.0
            content_str = json.dumps(ep.content).lower()
            if query_lower in content_str:
                score += 0.5
            for tag in ep.tags:
                if query_lower in tag.lower():
                    score += 0.3
            score += ep.importance * 0.2
            if score > 0:
                scored.append((score, ep))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": ep.id,
                "timestamp": ep.timestamp,
                "content": ep.content,
                "importance": ep.importance,
                "tags": ep.tags,
                "score": round(s, 3),
            }
            for s, ep in scored[:top_k]
        ]

    async def get_recent(self, limit: int = 20) -> list[dict]:
        recent = self._episodes[-limit:]
        recent.reverse()
        return [
            {
                "id": ep.id,
                "timestamp": ep.timestamp,
                "content": ep.content,
                "importance": ep.importance,
            }
            for ep in recent
        ]

    def save(self, path: Optional[str] = None):
        path = path or str(self._path)
        data = [
            {
                "id": e.id,
                "timestamp": e.timestamp,
                "content": e.content,
                "importance": e.importance,
                "tags": e.tags,
            }
            for e in self._episodes
        ]
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path: Optional[str] = None):
        path = path or str(self._path)
        p = Path(path)
        if p.exists():
            with open(path) as f:
                data = json.load(f)
            for item in data:
                self._episodes.append(Episode(**item))
