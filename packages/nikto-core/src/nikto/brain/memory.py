"""NIKTO Long-Term Memory — Persistent memory with graph connections, timeline, and semantic compression."""

import json
import heapq
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict, deque

try:
    from nikto.brain.models import MemoryFragment
except ImportError:
    try:
        from kyros.brain.models import MemoryFragment
    except ImportError:
        from dataclasses import dataclass, field, asdict
        @dataclass
        class MemoryFragment:
            content: str; tags: list = field(default_factory=list)
            importance: float = 0.5; emotional_valence: float = 0.0
            created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
            last_accessed: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
            access_count: int = 0; strength: float = 1.0
            id: str = field(default_factory=lambda: hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16])
            metadata: dict = field(default_factory=dict)
            def to_dict(self) -> dict: return asdict(self)
            def access(self): self.access_count += 1; self.last_accessed = datetime.now(timezone.utc).isoformat()
            def decay(self, rate=0.01): self.strength = max(0.0, self.strength - rate * (1.0 - self.importance))
            def reinforce(self, amount=0.1): self.strength = min(1.0, self.strength + amount)
            def __post_init__(self):
                self.importance = max(0.0, min(1.0, self.importance))
                self.strength = max(0.0, min(1.0, self.strength))
                self.emotional_valence = max(-1.0, min(1.0, self.emotional_valence))


class NiktoLongTermMemory:

    def __init__(self, max_size: int = 10000):
        self.fragments = {}
        self.max_size = max_size
        self.index = {}
        self.clusters = {}
        self.graph = defaultdict(set)
        self.timeline_index = []

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
        self._connect_to_graph(mem)
        self.timeline_index.append(mem.id)
        if len(self.fragments) > self.max_size:
            self._evict()
        return mem.id

    def _connect_to_graph(self, mem: MemoryFragment):
        for other_id, other in self.fragments.items():
            if other_id == mem.id:
                continue
            shared_tags = set(mem.tags) & set(other.tags)
            if shared_tags:
                self.graph[mem.id].add(other_id)
                self.graph[other_id].add(mem.id)

    # ── Graph Methods ─────────────────────────────────────────────────

    def get_connected(self, memory_id: str, depth: int = 1) -> dict:
        if memory_id not in self.fragments:
            return {"error": "Memory not found", "nodes": []}
        visited = {memory_id}
        queue = deque([(memory_id, 0)])
        nodes = []
        while queue:
            current, d = queue.popleft()
            if d >= depth:
                continue
            for neighbor in self.graph.get(current, set()):
                if neighbor not in visited and neighbor in self.fragments:
                    visited.add(neighbor)
                    mem = self.fragments[neighbor]
                    nodes.append({
                        "id": neighbor,
                        "content": mem.content[:80],
                        "tags": mem.tags,
                        "importance": mem.importance,
                        "distance": d + 1,
                    })
                    queue.append((neighbor, d + 1))
        return {"source_id": memory_id, "depth": depth, "connected_count": len(nodes), "nodes": nodes}

    def shortest_path(self, mem1_id: str, mem2_id: str) -> Optional[list]:
        if mem1_id not in self.fragments or mem2_id not in self.fragments:
            return None
        if mem1_id == mem2_id:
            return [mem1_id]
        queue = deque([(mem1_id, [mem1_id])])
        visited = {mem1_id}
        while queue:
            current, path = queue.popleft()
            for neighbor in self.graph.get(current, set()):
                if neighbor == mem2_id:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None

    def memory_graph_summary(self) -> dict:
        if not self.graph:
            return {"nodes": 0, "edges": 0, "avg_degree": 0}
        total_edges = sum(len(neighbors) for neighbors in self.graph.values())
        return {
            "nodes": len(self.graph),
            "edges": total_edges // 2,
            "avg_degree": round(total_edges / max(len(self.graph), 1), 2),
        }

    # ── Timeline Methods ──────────────────────────────────────────────

    def timeline(self, limit: int = 20, offset: int = 0) -> list:
        ids = self.timeline_index[offset:offset + limit]
        result = []
        for mid in ids:
            mem = self.fragments.get(mid)
            if mem:
                result.append(mem.to_dict())
        return result

    def timeline_between(self, start_iso: str, end_iso: str) -> list:
        result = []
        for mem in self.fragments.values():
            if start_iso <= mem.created <= end_iso:
                result.append(mem.to_dict())
        return sorted(result, key=lambda m: m["created"])

    def timeline_around(self, memory_id: str, window: int = 5) -> dict:
        if memory_id not in self.timeline_index:
            return {"error": "Memory not found in timeline"}
        idx = self.timeline_index.index(memory_id)
        start = max(0, idx - window)
        end = min(len(self.timeline_index), idx + window + 1)
        before = []
        after = []
        target = None
        for i in range(start, end):
            mid = self.timeline_index[i]
            mem = self.fragments.get(mid)
            if not mem:
                continue
            entry = {"id": mid, "content": mem.content[:80], "created": mem.created}
            if i < idx:
                before.append(entry)
            elif i > idx:
                after.append(entry)
            else:
                target = entry
        return {"target": target, "before": before, "after": after}

    # ── Semantic Compression ──────────────────────────────────────────

    def compress(self, tags: list = None, max_entries: int = 10) -> list:
        candidates = list(self.fragments.values())
        if tags:
            candidates = [m for m in candidates if any(t in m.tags for t in tags)]
        candidates.sort(key=lambda m: -m.importance)
        candidates = candidates[:max_entries]
        groups = defaultdict(list)
        for mem in candidates:
            primary_tag = mem.tags[0] if mem.tags else "general"
            groups[primary_tag].append(mem)
        summaries = []
        for tag, group in groups.items():
            group.sort(key=lambda m: -m.importance)
            total_importance = sum(m.importance for m in group)
            top = group[0]
            summaries.append({
                "tag": tag,
                "count": len(group),
                "total_importance": round(total_importance, 2),
                "compressed": f"[{tag}] {top.content[:150]} (+{len(group) - 1} related)",
                "time_span": f"{group[-1].created[:10]} to {group[0].created[:10]}",
            })
        return summaries

    # ── Core Methods ──────────────────────────────────────────────────

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
            self.graph.pop(memory_id, None)
            for neighbors in self.graph.values():
                neighbors.discard(memory_id)
            if memory_id in self.timeline_index:
                self.timeline_index.remove(memory_id)
            del self.fragments[memory_id]

    def consolidate(self):
        for mem in self.fragments.values():
            mem.decay(rate=0.005 * (1.0 - mem.importance))
        self._cluster()
        self._prune_graph()

    def _prune_graph(self):
        valid_ids = set(self.fragments.keys())
        for node_id in list(self.graph.keys()):
            if node_id not in valid_ids:
                del self.graph[node_id]
        for node_id in self.graph:
            self.graph[node_id] = {n for n in self.graph[node_id] if n in valid_ids}

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

    # ── Search Methods ────────────────────────────────────────────────

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
            "graph_nodes": len(self.graph),
            "graph_edges": sum(len(v) for v in self.graph.values()) // 2,
            "timeline_length": len(self.timeline_index),
            "avg_importance": sum(m.importance for m in self.fragments.values()) / max(len(self.fragments), 1),
            "avg_strength": sum(m.strength for m in self.fragments.values()) / max(len(self.fragments), 1),
        }

    def save(self) -> dict:
        return {
            "fragments": {vid: mem.to_dict() for vid, mem in self.fragments.items()},
            "max_size": self.max_size,
            "graph": {k: list(v) for k, v in self.graph.items()},
            "timeline_index": self.timeline_index[:],
        }

    def load(self, data: dict):
        self.max_size = data.get("max_size", 10000)
        self.fragments = {}
        self.index = {}
        self.clusters = {}
        self.graph = defaultdict(set)
        self.timeline_index = data.get("timeline_index", [])
        for vid, mem_dict in data.get("fragments", {}).items():
            mem = MemoryFragment(**mem_dict)
            self.fragments[vid] = mem
            for tag in mem.tags:
                if tag not in self.index:
                    self.index[tag] = []
                self.index[tag].append(vid)
        for node_id, neighbors in data.get("graph", {}).items():
            self.graph[node_id] = set(neighbors)
        self._cluster()

    def export(self) -> dict:
        return {vid: mem.to_dict() for vid, mem in self.fragments.items()}

    def import_memories(self, data: dict):
        for vid, mem_dict in data.items():
            if vid in self.fragments:
                continue
            mem = MemoryFragment(**mem_dict)
            self.fragments[vid] = mem
            for tag in mem.tags:
                if tag not in self.index:
                    self.index[tag] = []
                self.index[tag].append(vid)
            self._connect_to_graph(mem)
            self.timeline_index.append(vid)
