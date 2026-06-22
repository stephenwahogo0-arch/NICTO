"""NICTO X — High-performance vector store with numpy-based embeddings and cosine similarity."""

from __future__ import annotations

import json
import logging
import math
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("nicto_x.knowledge.vector_store")


class VectorStore:
    """In-memory vector store with numpy-powered embeddings and fast cosine search."""

    def __init__(self, dim: int = 768, store_path: str = ""):
        self.dim = dim
        self._path = store_path or str(Path.home() / ".nicto-x" / "vectors.json")
        self._documents: list[dict] = []
        self._vectors: list[list[float]] = []
        self._index: dict[str, list[int]] = {}

    def add(self, doc_id: str, content: str, metadata: Optional[dict] = None):
        vec = self._embed(content)
        self._documents.append({"id": doc_id, "content": content, "metadata": metadata or {}, "timestamp": time.time()})
        self._vectors.append(vec)
        for word in content.lower().split()[:20]:
            self._index.setdefault(word, []).append(len(self._documents) - 1)

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        query_vec = self._embed(query)
        scores: list[tuple[float, int]] = []

        candidates = self._get_candidates(query)
        if candidates:
            for idx in candidates:
                sim = self._cosine_similarity(query_vec, self._vectors[idx])
                scores.append((sim, idx))
        else:
            for i, vec in enumerate(self._vectors):
                sim = self._cosine_similarity(query_vec, vec)
                scores.append((sim, i))

        scores.sort(key=lambda x: x[0], reverse=True)
        results = []
        for sim, idx in scores[:top_k]:
            doc = dict(self._documents[idx])
            doc["score"] = round(sim, 4)
            results.append(doc)
        return results

    def search_batch(self, queries: list[str], top_k: int = 5) -> list[list[dict]]:
        return [self.search(q, top_k) for q in queries]

    def _get_candidates(self, query: str) -> Optional[set[int]]:
        words = query.lower().split()
        matched = None
        for w in words:
            if w in self._index:
                idx_set = set(self._index[w])
                if matched is None:
                    matched = idx_set
                else:
                    matched &= idx_set
        return matched

    def count(self) -> int:
        return len(self._documents)

    def _embed(self, text: str) -> list[float]:
        words = text.lower().split()[:256]
        if not words:
            return [0.0] * self.dim

        vec = [0.0] * self.dim
        ngram_counts = {}
        for i in range(len(words)):
            for size in (1, 2, 3):
                if i + size <= len(words):
                    ngram = " ".join(words[i:i + size])
                    ngram_counts[ngram] = ngram_counts.get(ngram, 0) + 1

        bound = max(self.dim, 1)
        for ngram, count in ngram_counts.items():
            h = abs(hash(ngram)) % bound
            vec[h] += count / max(len(words), 1)

        for i, word in enumerate(words):
            h = abs(hash(word + str(i // 2))) % bound
            pos = (len(words) - i) / max(len(words), 1)
            vec[h] += pos * 0.5

        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        try:
            import numpy as np
            na = np.array(a, dtype=np.float64)
            nb = np.array(b, dtype=np.float64)
            dot = float(np.dot(na, nb))
            norma = float(np.linalg.norm(na))
            normb = float(np.linalg.norm(nb))
        except ImportError:
            dot = sum(x * y for x, y in zip(a, b))
            norma = math.sqrt(sum(x * x for x in a))
            normb = math.sqrt(sum(y * y for y in b))
        if norma == 0 or normb == 0:
            return 0.0
        return dot / (norma * normb)

    def save(self):
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump({"documents": self._documents, "dim": self.dim, "index": {k: v for k, v in self._index.items()}}, f)

    def load(self):
        p = Path(self._path)
        if p.exists():
            with open(self._path) as f:
                data = json.load(f)
            self._documents = data.get("documents", [])
            self.dim = data.get("dim", 768)
            self._index = data.get("index", {})
            for doc in self._documents:
                self._vectors.append(self._embed(doc["content"]))
