import json
import heapq
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional
from kyros.brain.models import MemoryFragment


class NiktoLongTermMemory:

    def __init__(self, max_size: int = 10000):
        self.fragments = {}
        self.max_size = max_size
        self.index = {}
        self.clusters = {}

    def store(self, content: str, tags: list = None, importance: float = 0.5,
              emotional_valence: float = 0.0) -> str:
        mem = MemoryFragment(
            content=content,
            tags=tags or [],
            importance=max(0.0, min(1.0, importance)),
            emotional_valence=max(-1.0, min(1.0, emotional_valence)),
        )
        self.fragments[mem.id] = mem
        for tag in mem.tags:
            if tag not in self.index:
                self.index[tag] = []
            self.index[tag].append(mem.id)
        if len(self.fragments) > self.max_size:
            self._evict()
        return mem.id

    def recall(self, query: str, top_k: int = 10) -> list:
        q = query.lower()
        scored = []
        for mem in self.fragments.values():
            score = 0.0
            if q in mem.content.lower():
                score += mem.importance * 0.5
                score += (len(q) / max(len(mem.content), 1)) * 0.3
            for tag in mem.tags:
                if q in tag.lower():
                    score += 0.2
            score *= mem.strength
            score *= (1.0 + 0.1 * mem.access_count)
            if score > 0:
                scored.append((score, mem))
        scored.sort(key=lambda x: -x[0])
        top = scored[:top_k]
        for _, mem in top:
            mem.access()
        return [mem.to_dict() for _, mem in top]

    def remember(self, memory_id: str) -> Optional[dict]:
        if memory_id in self.fragments:
            self.fragments[memory_id].access()
            return self.fragments[memory_id].to_dict()
        return None

    def forget(self, memory_id: str):
        if memory_id in self.fragments:
            mem = self.fragments[memory_id]
            for tag in mem.tags:
                if tag in self.index and memory_id in self.index[tag]:
                    self.index[tag].remove(memory_id)
            del self.fragments[memory_id]

    def consolidate(self):
        for mem in self.fragments.values():
            mem.decay(rate=0.005 * (1.0 - mem.importance))
        self._cluster()

    def _cluster(self):
        self.clusters = {}
        for mem in self.fragments.values():
            for tag in mem.tags:
                if tag not in self.clusters:
                    self.clusters[tag] = []
                self.clusters[tag].append(mem.id)

    def _evict(self):
        scored = [(mem.strength * mem.importance, mem.id) for mem in self.fragments.values()]
        heapq.heapify(scored)
        while len(self.fragments) > self.max_size * 0.9:
            _, vid = heapq.heappop(scored)
            self.forget(vid)

    def search_by_tag(self, tag: str) -> list:
        ids = self.index.get(tag, [])
        return [self.fragments[vid].to_dict() for vid in ids if vid in self.fragments]

    def search_by_emotional_valence(self, min_valence: float = -1.0, max_valence: float = 1.0) -> list:
        return [
            mem.to_dict() for mem in self.fragments.values()
            if min_valence <= mem.emotional_valence <= max_valence
        ]

    def search_by_importance(self, min_importance: float = 0.0) -> list:
        return [
            mem.to_dict() for mem in self.fragments.values()
            if mem.importance >= min_importance
        ]

    def summarize(self) -> dict:
        return {
            "total_memories": len(self.fragments),
            "unique_tags": len(self.index),
            "clusters": len(self.clusters),
            "avg_importance": sum(m.importance for m in self.fragments.values()) / max(len(self.fragments), 1),
            "avg_strength": sum(m.strength for m in self.fragments.values()) / max(len(self.fragments), 1),
        }

    def save(self) -> dict:
        return {
            "fragments": {vid: mem.to_dict() for vid, mem in self.fragments.items()},
            "max_size": self.max_size,
        }

    def load(self, data: dict):
        self.max_size = data.get("max_size", 10000)
        self.fragments = {}
        self.index = {}
        self.clusters = {}
        for vid, mem_dict in data.get("fragments", {}).items():
            mem = MemoryFragment(**mem_dict)
            self.fragments[vid] = mem
            for tag in mem.tags:
                if tag not in self.index:
                    self.index[tag] = []
                self.index[tag].append(vid)
        self._cluster()

    def export(self) -> dict:
        return {vid: mem.to_dict() for vid, mem in self.fragments.items()}

    def import_memories(self, data: dict):
        for vid, mem_dict in data.items():
            mem = MemoryFragment(**mem_dict)
            self.fragments[vid] = mem
            for tag in mem.tags:
                if tag not in self.index:
                    self.index[tag] = []
                self.index[tag].append(vid)
