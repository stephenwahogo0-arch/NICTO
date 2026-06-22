from .base import MemoryStore, MemoryEntry
from typing import Any, Dict, List, Optional, Tuple
import json
import time
import os
import statistics


class PerformanceMemory(MemoryStore):
    def __init__(self, store_name: str = "performance", base_path: Optional[str] = None):
        super().__init__(store_name, base_path)

    def _init_db(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS performance (
                perf_id TEXT PRIMARY KEY,
                brain TEXT NOT NULL,
                domain TEXT NOT NULL,
                task_type TEXT DEFAULT '',
                accuracy REAL DEFAULT 0.0,
                elo_before REAL DEFAULT 1000.0,
                elo_after REAL DEFAULT 1000.0,
                latency_ms REAL DEFAULT 0.0,
                timestamp REAL NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_perf_brain_domain
            ON performance(brain, domain)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_perf_timestamp
            ON performance(timestamp)
        """)
        self._conn.commit()

    def log_performance(
        self,
        brain: str,
        domain: str,
        accuracy: float,
        elo_before: float,
        elo_after: float,
        task_type: str = "",
        latency_ms: float = 0.0,
        metadata: Optional[Dict] = None,
    ) -> str:
        perf_id = f"perf_{int(time.time() * 1e6)}"
        self._conn.execute(
            """
            INSERT INTO performance
            (perf_id, brain, domain, task_type, accuracy, elo_before, elo_after, latency_ms, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                perf_id,
                brain,
                domain,
                task_type,
                accuracy,
                elo_before,
                elo_after,
                latency_ms,
                time.time(),
                json.dumps(metadata or {}),
            ),
        )
        self._conn.commit()
        return perf_id

    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        md = metadata or {}
        if isinstance(value, dict):
            return self.log_performance(
                brain=value.get("brain", md.get("brain", "unknown")),
                domain=value.get("domain", md.get("domain", "general")),
                accuracy=value.get("accuracy", 0.0),
                elo_before=value.get("elo_before", 1000.0),
                elo_after=value.get("elo_after", 1000.0),
                task_type=value.get("task_type", md.get("task_type", "")),
                latency_ms=value.get("latency_ms", md.get("latency_ms", 0.0)),
                metadata=md,
            )
        return self.log_performance(
            brain=key,
            domain=md.get("domain", "general"),
            accuracy=float(value) if isinstance(value, (int, float)) else 0.0,
            elo_before=md.get("elo_before", 1000.0),
            elo_after=md.get("elo_after", 1000.0),
            metadata=md,
        )

    def get_brain_stats(self, brain: str, domain: Optional[str] = None) -> Dict:
        if domain:
            rows = self._conn.execute(
                "SELECT accuracy, elo_after, latency_ms FROM performance WHERE brain = ? AND domain = ?",
                (brain, domain),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT accuracy, elo_after, latency_ms FROM performance WHERE brain = ?",
                (brain,),
            ).fetchall()
        if not rows:
            return {"brain": brain, "domain": domain, "count": 0}
        accuracies = [r[0] for r in rows]
        elos = [r[1] for r in rows]
        latencies = [r[2] for r in rows]
        return {
            "brain": brain,
            "domain": domain,
            "count": len(rows),
            "avg_accuracy": statistics.mean(accuracies) if accuracies else 0.0,
            "max_accuracy": max(accuracies) if accuracies else 0.0,
            "min_accuracy": min(accuracies) if accuracies else 0.0,
            "latest_elo": elos[-1] if elos else 1000.0,
            "max_elo": max(elos) if elos else 1000.0,
            "avg_elo": statistics.mean(elos) if elos else 1000.0,
            "avg_latency_ms": statistics.mean(latencies) if latencies else 0.0,
            "total_elo_change": elos[-1] - elos[0] if len(elos) > 1 else 0.0,
        }

    def domain_rankings(self, domain: str) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT brain, AVG(accuracy) as avg_acc, AVG(elo_after) as avg_elo, COUNT(*) as cnt FROM performance WHERE domain = ? GROUP BY brain ORDER BY avg_acc DESC",
            (domain,),
        ).fetchall()
        return [
            {
                "brain": r[0],
                "avg_accuracy": r[1],
                "avg_elo": r[2],
                "samples": r[3],
            }
            for r in rows
        ]

    def accuracy_trend(self, brain: str, domain: str, n: int = 50) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT accuracy, elo_after, latency_ms, timestamp FROM performance WHERE brain = ? AND domain = ? ORDER BY timestamp DESC LIMIT ?",
            (brain, domain, n),
        ).fetchall()
        result = []
        for r in reversed(rows):
            result.append({
                "accuracy": r[0],
                "elo": r[1],
                "latency_ms": r[2],
                "timestamp": r[3],
            })
        return result

    def query(self, query_text: str = "", limit: int = 10) -> List[Dict]:
        like = f"%{query_text}%"
        rows = self._conn.execute(
            "SELECT perf_id, brain, domain, task_type, accuracy, elo_before, elo_after, latency_ms, timestamp, metadata FROM performance WHERE brain LIKE ? OR domain LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (like, like, limit),
        ).fetchall()
        return [
            {
                "perf_id": r[0],
                "brain": r[1],
                "domain": r[2],
                "task_type": r[3],
                "accuracy": r[4],
                "elo_before": r[5],
                "elo_after": r[6],
                "latency_ms": r[7],
                "timestamp": r[8],
                "metadata": json.loads(r[9]) if r[9] else {},
            }
            for r in rows
        ]

    def recall(self, key: str) -> Optional[Any]:
        return self.get_brain_stats(key)

    def forget(self, key: str) -> bool:
        c = self._conn.execute("DELETE FROM performance WHERE perf_id = ?", (key,))
        self._conn.commit()
        return c.rowcount > 0

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM performance").fetchone()
        return row[0] if row else 0

    def clear(self) -> None:
        self._conn.execute("DELETE FROM performance")
        self._conn.commit()
