"""NICTO X — Semantic memory: stores facts, concepts, and learned patterns."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from nicto_x.core.config import MemoryConfig

logger = logging.getLogger("nicto_x.memory.semantic")


@dataclass
class Fact:
    id: str = ""
    subject: str = ""
    predicate: str = ""
    object_val: str = ""
    confidence: float = 0.8
    source: str = ""
    timestamp: float = field(default_factory=time.time)
    embedding: Optional[list[float]] = None


class SemanticMemory:
    """Stores facts, concepts, knowledge triples, and learned patterns."""

    def __init__(self, config: MemoryConfig):
        self.config = config
        self._facts: list[Fact] = []
        self._concepts: dict[str, set[str]] = {}
        self._path = Path.home() / ".nicto-x" / "semantic.json"

    def __len__(self) -> int:
        return len(self._facts)

    async def store_fact(
        self,
        subject: str,
        predicate: str,
        object_val: str,
        confidence: float = 0.8,
        source: str = "",
    ) -> str:
        fact = Fact(
            id=f"fact_{int(time.time() * 1000)}_{len(self._facts)}",
            subject=subject.lower().strip(),
            predicate=predicate.lower().strip(),
            object_val=object_val,
            confidence=confidence,
            source=source,
        )
        self._facts.append(fact)
        self._concepts.setdefault(fact.subject, set()).add(fact.predicate)
        if len(self._facts) > self.config.semantic_capacity:
            self._facts.sort(key=lambda f: f.confidence)
            self._facts = self._facts[-self.config.semantic_capacity:]
        return fact.id

    async def query(self, subject: str, predicate: Optional[str] = None) -> list[dict]:
        subject_lower = subject.lower().strip()
        results = []
        for fact in self._facts:
            if fact.subject == subject_lower:
                if predicate is None or fact.predicate == predicate.lower().strip():
                    results.append({
                        "id": fact.id,
                        "subject": fact.subject,
                        "predicate": fact.predicate,
                        "object": fact.object_val,
                        "confidence": fact.confidence,
                        "source": fact.source,
                    })
        return results

    async def search(self, query: str, top_k: int = 10) -> list[dict]:
        query_lower = query.lower()
        scored = []
        for fact in self._facts:
            score = 0.0
            if query_lower in fact.subject:
                score += 1.0
            if query_lower in fact.predicate:
                score += 0.8
            if query_lower in fact.object_val.lower():
                score += 0.5
            score *= fact.confidence
            if score > 0:
                scored.append((score, fact))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": f.id,
                "subject": f.subject,
                "predicate": f.predicate,
                "object": f.object_val,
                "confidence": f.confidence,
                "source": f.source,
                "score": round(s, 3),
            }
            for s, f in scored[:top_k]
        ]

    def get_concepts(self) -> dict[str, list[str]]:
        return {k: list(v) for k, v in self._concepts.items()}

    def save(self, path: Optional[str] = None):
        path = path or str(self._path)
        data = [
            {
                "id": f.id,
                "subject": f.subject,
                "predicate": f.predicate,
                "object_val": f.object_val,
                "confidence": f.confidence,
                "source": f.source,
                "timestamp": f.timestamp,
            }
            for f in self._facts
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
                self._facts.append(Fact(**item))
                self._concepts.setdefault(item["subject"], set()).add(item["predicate"])
