"""NICTO X — Knowledge graph engine for structured fact storage."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("nicto_x.knowledge.graph")


class KnowledgeGraph:
    """NetworkX-based knowledge graph with entity-relation storage and traversal."""

    def __init__(self, store_path: str = ""):
        self._path = store_path or str(Path.home() / ".nicto-x" / "knowledge_graph.json")
        self._nodes: dict[str, dict] = {}
        self._edges: list[dict] = []

    def add_node(self, node_id: str, label: str = "", properties: Optional[dict] = None):
        self._nodes[node_id] = {
            "id": node_id,
            "label": label or node_id,
            "properties": properties or {},
        }

    def add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        weight: float = 1.0,
        properties: Optional[dict] = None,
    ):
        self._edges.append({
            "source": source,
            "target": target,
            "relation": relation,
            "weight": weight,
            "properties": properties or {},
        })

    def query(self, query: str, limit: int = 20) -> list[dict]:
        q = query.lower()
        results = []
        for node_id, node in self._nodes.items():
            if q in node_id.lower() or q in node.get("label", "").lower():
                results.append({"type": "node", **node})
        for edge in self._edges:
            if q in edge["relation"].lower():
                results.append({"type": "edge", **edge})
        return results[:limit]

    def get_neighbors(self, node_id: str, max_depth: int = 2) -> list[dict]:
        visited = set()
        results = []
        queue = [(node_id, 0)]
        while queue:
            current, depth = queue.pop(0)
            if current in visited or depth > max_depth:
                continue
            visited.add(current)
            if current in self._nodes:
                results.append(self._nodes[current])
            for edge in self._edges:
                if edge["source"] == current and edge["target"] not in visited:
                    queue.append((edge["target"], depth + 1))
                if edge["target"] == current and edge["source"] not in visited:
                    queue.append((edge["source"], depth + 1))
        return results

    def get_stats(self) -> dict:
        return {"nodes": len(self._nodes), "edges": len(self._edges)}

    def save(self):
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump({"nodes": self._nodes, "edges": self._edges}, f, indent=2)

    def load(self):
        p = Path(self._path)
        if p.exists():
            with open(self._path) as f:
                data = json.load(f)
            self._nodes = data.get("nodes", {})
            self._edges = data.get("edges", [])
