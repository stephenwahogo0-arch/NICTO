from .base import MemoryStore, MemoryEntry
from typing import Any, Dict, List, Optional, Tuple
import json
import time
import math
import os
import hashlib


class TaskFeatureMemory(MemoryStore):
    def __init__(self, store_name: str = "task_features", base_path: Optional[str] = None):
        super().__init__(store_name, base_path)

    def _init_db(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS task_features (
                task_hash TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                domain TEXT NOT NULL,
                complexity REAL DEFAULT 0.5,
                feature_vector TEXT DEFAULT '[]',
                brain_used TEXT DEFAULT '',
                outcome_score REAL DEFAULT 0.0,
                timestamp REAL NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tf_domain
            ON task_features(domain)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tf_type
            ON task_features(task_type)
        """)
        self._conn.commit()

    def _make_hash(self, task_type: str, domain: str, feature_vector: List[float]) -> str:
        raw = f"{task_type}:{domain}:{json.dumps(feature_vector, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def store_task_features(
        self,
        task_type: str,
        domain: str,
        feature_vector: List[float],
        brain_used: str = "",
        outcome_score: float = 0.0,
        complexity: float = 0.5,
        metadata: Optional[Dict] = None,
    ) -> str:
        task_hash = self._make_hash(task_type, domain, feature_vector)
        self._conn.execute(
            """
            INSERT OR REPLACE INTO task_features
            (task_hash, task_type, domain, complexity, feature_vector, brain_used, outcome_score, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_hash,
                task_type,
                domain,
                complexity,
                json.dumps(feature_vector),
                brain_used,
                outcome_score,
                time.time(),
                json.dumps(metadata or {}),
            ),
        )
        self._conn.commit()
        return task_hash

    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        md = metadata or {}
        if isinstance(value, dict):
            return self.store_task_features(
                task_type=value.get("task_type", md.get("task_type", "unknown")),
                domain=value.get("domain", md.get("domain", "general")),
                feature_vector=value.get("feature_vector", md.get("feature_vector", [])),
                brain_used=value.get("brain_used", md.get("brain_used", "")),
                outcome_score=value.get("outcome_score", md.get("outcome_score", 0.0)),
                complexity=value.get("complexity", md.get("complexity", 0.5)),
                metadata=md,
            )
        return self.store_task_features(
            task_type=md.get("task_type", "unknown"),
            domain=md.get("domain", "general"),
            feature_vector=md.get("feature_vector", []),
            brain_used=key,
            outcome_score=float(value) if isinstance(value, (int, float)) else 0.0,
            complexity=md.get("complexity", 0.5),
            metadata=md,
        )

    def similar_tasks(
        self, feature_vector: List[float], limit: int = 10
    ) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT task_hash, task_type, domain, complexity, feature_vector, brain_used, outcome_score, timestamp, metadata FROM task_features ORDER BY timestamp DESC LIMIT 2000"
        ).fetchall()
        scored = []
        for r in rows:
            fv = json.loads(r[4]) if r[4] else []
            if fv:
                dot = sum(a * b for a, b in zip(feature_vector, fv))
                na = math.sqrt(sum(x * x for x in feature_vector))
                nb = math.sqrt(sum(y * y for y in fv))
                sim = dot / (na * nb) if na > 0 and nb > 0 else 0.0
                scored.append((sim, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for _, r in scored[:limit]:
            results.append({
                "task_hash": r[0],
                "task_type": r[1],
                "domain": r[2],
                "complexity": r[3],
                "feature_vector": json.loads(r[4]) if r[4] else [],
                "brain_used": r[5],
                "outcome_score": r[6],
                "timestamp": r[7],
                "metadata": json.loads(r[8]) if r[8] else {},
                "similarity": _,
            })
        return results

    def routing_history(self, domain: str, n: int = 100) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT task_hash, task_type, domain, complexity, feature_vector, brain_used, outcome_score, timestamp, metadata FROM task_features WHERE domain = ? ORDER BY timestamp DESC LIMIT ?",
            (domain, n),
        ).fetchall()
        return [
            {
                "task_hash": r[0],
                "task_type": r[1],
                "domain": r[2],
                "complexity": r[3],
                "feature_vector": json.loads(r[4]) if r[4] else [],
                "brain_used": r[5],
                "outcome_score": r[6],
                "timestamp": r[7],
                "metadata": json.loads(r[8]) if r[8] else {},
            }
            for r in rows
        ]

    def best_brain_for(self, domain: str, task_type: str) -> Optional[str]:
        rows = self._conn.execute(
            "SELECT brain_used, AVG(outcome_score) as avg_score, COUNT(*) as cnt FROM task_features WHERE domain = ? AND task_type = ? AND brain_used != '' GROUP BY brain_used ORDER BY avg_score DESC LIMIT 1",
            (domain, task_type),
        ).fetchall()
        if rows:
            return {
                "brain": rows[0][0],
                "avg_score": rows[0][1],
                "samples": rows[0][2],
            }
        return None

    def query(self, query_text: str = "", limit: int = 10) -> List[Dict]:
        like = f"%{query_text}%"
        rows = self._conn.execute(
            "SELECT task_hash, task_type, domain, complexity, feature_vector, brain_used, outcome_score, timestamp, metadata FROM task_features WHERE task_type LIKE ? OR domain LIKE ? OR brain_used LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (like, like, like, limit),
        ).fetchall()
        return [
            {
                "task_hash": r[0],
                "task_type": r[1],
                "domain": r[2],
                "complexity": r[3],
                "feature_vector": json.loads(r[4]) if r[4] else [],
                "brain_used": r[5],
                "outcome_score": r[6],
                "timestamp": r[7],
                "metadata": json.loads(r[8]) if r[8] else {},
            }
            for r in rows
        ]

    def recall(self, key: str) -> Optional[Any]:
        row = self._conn.execute(
            "SELECT task_hash, task_type, domain, complexity, feature_vector, brain_used, outcome_score, timestamp, metadata FROM task_features WHERE task_hash = ?",
            (key,),
        ).fetchone()
        if row:
            return {
                "task_hash": row[0],
                "task_type": row[1],
                "domain": row[2],
                "complexity": row[3],
                "feature_vector": json.loads(row[4]) if row[4] else [],
                "brain_used": row[5],
                "outcome_score": row[6],
                "timestamp": row[7],
                "metadata": json.loads(row[8]) if row[8] else {},
            }
        return None

    def forget(self, key: str) -> bool:
        c = self._conn.execute("DELETE FROM task_features WHERE task_hash = ?", (key,))
        self._conn.commit()
        return c.rowcount > 0

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM task_features").fetchone()
        return row[0] if row else 0

    def clear(self) -> None:
        self._conn.execute("DELETE FROM task_features")
        self._conn.commit()
