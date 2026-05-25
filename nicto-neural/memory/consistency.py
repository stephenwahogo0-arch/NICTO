from .base import MemoryStore, MemoryEntry
from typing import Any, Dict, List, Optional, Tuple
import json
import time
import os
import statistics


class ConsistencyMemory(MemoryStore):
    def __init__(self, store_name: str = "consistency", base_path: Optional[str] = None):
        super().__init__(store_name, base_path)

    def _init_db(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS consistency (
                record_id TEXT PRIMARY KEY,
                brain TEXT NOT NULL,
                domain TEXT NOT NULL,
                coherence_score REAL DEFAULT 0.5,
                stability_score REAL DEFAULT 0.5,
                contradictions INTEGER DEFAULT 0,
                samples INTEGER DEFAULT 1,
                timestamp REAL NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cons_brain_domain
            ON consistency(brain, domain)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cons_timestamp
            ON consistency(timestamp)
        """)
        self._conn.commit()

    def log_consistency(
        self,
        brain: str,
        domain: str,
        coherence_score: float,
        stability_score: float,
        contradictions: int = 0,
        metadata: Optional[Dict] = None,
    ) -> str:
        record_id = f"cons_{int(time.time() * 1e6)}"
        self._conn.execute(
            """
            INSERT INTO consistency
            (record_id, brain, domain, coherence_score, stability_score, contradictions, samples, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                brain,
                domain,
                min(max(coherence_score, 0.0), 1.0),
                min(max(stability_score, 0.0), 1.0),
                contradictions,
                1,
                time.time(),
                json.dumps(metadata or {}),
            ),
        )
        self._conn.commit()
        return record_id

    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        md = metadata or {}
        if isinstance(value, dict):
            return self.log_consistency(
                brain=value.get("brain", md.get("brain", key)),
                domain=value.get("domain", md.get("domain", "general")),
                coherence_score=value.get("coherence_score", md.get("coherence_score", 0.5)),
                stability_score=value.get("stability_score", md.get("stability_score", 0.5)),
                contradictions=value.get("contradictions", md.get("contradictions", 0)),
                metadata=md,
            )
        return self.log_consistency(
            brain=key,
            domain=md.get("domain", "general"),
            coherence_score=md.get("coherence_score", 0.5),
            stability_score=md.get("stability_score", 0.5),
            contradictions=md.get("contradictions", 0),
            metadata=md,
        )

    def get_consistency(self, brain: str, domain: str) -> Optional[Dict]:
        rows = self._conn.execute(
            "SELECT coherence_score, stability_score, contradictions, samples, timestamp FROM consistency WHERE brain = ? AND domain = ? ORDER BY timestamp DESC LIMIT 1",
            (brain, domain),
        ).fetchall()
        if rows:
            r = rows[0]
            return {
                "brain": brain,
                "domain": domain,
                "coherence_score": r[0],
                "stability_score": r[1],
                "contradictions": r[2],
                "samples": r[3],
                "timestamp": r[4],
            }
        return None

    def consistency_trend(self, brain: str, domain: str, n: int = 20) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT coherence_score, stability_score, contradictions, timestamp FROM consistency WHERE brain = ? AND domain = ? ORDER BY timestamp DESC LIMIT ?",
            (brain, domain, n),
        ).fetchall()
        result = []
        for r in reversed(rows):
            result.append({
                "coherence_score": r[0],
                "stability_score": r[1],
                "contradictions": r[2],
                "timestamp": r[3],
            })
        return result

    def brains_by_consistency(self, domain: str) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT brain, AVG(coherence_score) as avg_coherence, AVG(stability_score) as avg_stability, SUM(contradictions) as total_contradictions, COUNT(*) as samples FROM consistency WHERE domain = ? GROUP BY brain ORDER BY avg_coherence DESC",
            (domain,),
        ).fetchall()
        return [
            {
                "brain": r[0],
                "avg_coherence": r[1],
                "avg_stability": r[2],
                "total_contradictions": r[3],
                "samples": r[4],
            }
            for r in rows
        ]

    def query(self, query_text: str = "", limit: int = 10) -> List[Dict]:
        like = f"%{query_text}%"
        rows = self._conn.execute(
            "SELECT record_id, brain, domain, coherence_score, stability_score, contradictions, samples, timestamp, metadata FROM consistency WHERE brain LIKE ? OR domain LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (like, like, limit),
        ).fetchall()
        return [
            {
                "record_id": r[0],
                "brain": r[1],
                "domain": r[2],
                "coherence_score": r[3],
                "stability_score": r[4],
                "contradictions": r[5],
                "samples": r[6],
                "timestamp": r[7],
                "metadata": json.loads(r[8]) if r[8] else {},
            }
            for r in rows
        ]

    def recall(self, key: str) -> Optional[Any]:
        parts = key.split("/")
        if len(parts) == 2:
            return self.get_consistency(parts[0], parts[1])
        row = self._conn.execute(
            "SELECT record_id, brain, domain, coherence_score, stability_score, contradictions, samples, timestamp, metadata FROM consistency WHERE record_id = ?",
            (key,),
        ).fetchone()
        if row:
            return {
                "record_id": row[0],
                "brain": row[1],
                "domain": row[2],
                "coherence_score": row[3],
                "stability_score": row[4],
                "contradictions": row[5],
                "samples": row[6],
                "timestamp": row[7],
                "metadata": json.loads(row[8]) if row[8] else {},
            }
        return None

    def forget(self, key: str) -> bool:
        c = self._conn.execute("DELETE FROM consistency WHERE record_id = ?", (key,))
        self._conn.commit()
        return c.rowcount > 0

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM consistency").fetchone()
        return row[0] if row else 0

    def clear(self) -> None:
        self._conn.execute("DELETE FROM consistency")
        self._conn.commit()
