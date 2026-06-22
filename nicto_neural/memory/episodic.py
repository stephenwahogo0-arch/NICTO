from .base import MemoryStore, MemoryEntry
from typing import Any, Dict, List, Optional, Tuple
import json
import time
import math
import os


class EpisodicMemory(MemoryStore):
    def __init__(self, store_name: str = "episodic", base_path: Optional[str] = None):
        super().__init__(store_name, base_path)

    def _init_db(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                event_id TEXT PRIMARY KEY,
                sequence_id TEXT NOT NULL,
                brain TEXT DEFAULT '',
                domain TEXT DEFAULT '',
                action TEXT DEFAULT '',
                outcome TEXT DEFAULT '',
                reward REAL DEFAULT 0.0,
                timestamp REAL NOT NULL,
                value TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                embedding TEXT DEFAULT '[]'
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ep_sequence
            ON episodes(sequence_id)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ep_timestamp
            ON episodes(timestamp)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ep_domain
            ON episodes(domain)
        """)
        self._conn.commit()

    def _cosine_sim(self, a: List[float], b: List[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def store(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict] = None,
    ) -> str:
        event_id = key or f"evt_{int(time.time() * 1e6)}"
        md = metadata or {}
        entry = MemoryEntry(
            key=event_id,
            value=value,
            metadata=md,
            timestamp=md.get("timestamp", time.time()),
            embedding=md.get("embedding", []),
        )
        self._conn.execute(
            """
            INSERT OR REPLACE INTO episodes
            (event_id, sequence_id, brain, domain, action, outcome, reward, timestamp, value, metadata, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                md.get("sequence_id", ""),
                md.get("brain", ""),
                md.get("domain", ""),
                md.get("action", ""),
                md.get("outcome", ""),
                md.get("reward", 0.0),
                entry.timestamp,
                json.dumps(value) if not isinstance(value, str) else value,
                json.dumps(md),
                json.dumps(entry.embedding),
            ),
        )
        self._conn.commit()
        return event_id

    def store_sequence(self, events: List[Dict]) -> List[str]:
        seq_id = f"seq_{int(time.time() * 1e6)}"
        ids = []
        for i, evt in enumerate(events):
            evt["sequence_id"] = seq_id
            evt["timestamp"] = evt.get("timestamp", time.time() + i * 0.001)
            key = evt.get("event_id", f"{seq_id}_{i}")
            ids.append(self.store(key, evt.get("value", ""), metadata=evt))
        return ids

    def query(self, query_text: str = "", limit: int = 10) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT event_id, sequence_id, brain, domain, action, outcome, reward, timestamp, value, metadata, embedding FROM episodes ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        results = []
        for row in rows:
            results.append({
                "event_id": row[0],
                "sequence_id": row[1],
                "brain": row[2],
                "domain": row[3],
                "action": row[4],
                "outcome": row[5],
                "reward": row[6],
                "timestamp": row[7],
                "value": row[8],
                "metadata": json.loads(row[9]) if row[9] else {},
                "embedding": json.loads(row[10]) if row[10] else [],
            })
        if query_text and results and results[0].get("embedding"):
            query_emb = results[0]["embedding"]
            scored = []
            for r in results:
                if r.get("embedding"):
                    sim = self._cosine_sim(query_emb, r["embedding"])
                    scored.append((sim, r))
            scored.sort(key=lambda x: x[0], reverse=True)
            results = [r for _, r in scored[:limit]]
        return results[:limit]

    def recall(self, key: str) -> Optional[Any]:
        row = self._conn.execute(
            "SELECT value FROM episodes WHERE event_id = ?", (key,)
        ).fetchone()
        if row:
            try:
                return json.loads(row[0])
            except (json.JSONDecodeError, TypeError):
                return row[0]
        return None

    def get_sequence(self, seq_id: str) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT event_id, sequence_id, brain, domain, action, outcome, reward, timestamp, value, metadata, embedding FROM episodes WHERE sequence_id = ? ORDER BY timestamp ASC",
            (seq_id,),
        ).fetchall()
        return [
            {
                "event_id": r[0],
                "sequence_id": r[1],
                "brain": r[2],
                "domain": r[3],
                "action": r[4],
                "outcome": r[5],
                "reward": r[6],
                "timestamp": r[7],
                "value": r[8],
                "metadata": json.loads(r[9]) if r[9] else {},
                "embedding": json.loads(r[10]) if r[10] else [],
            }
            for r in rows
        ]

    def recent(self, n: int = 10) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT event_id, sequence_id, brain, domain, action, outcome, reward, timestamp, value, metadata, embedding FROM episodes ORDER BY timestamp DESC LIMIT ?",
            (n,),
        ).fetchall()
        return [
            {
                "event_id": r[0],
                "sequence_id": r[1],
                "brain": r[2],
                "domain": r[3],
                "action": r[4],
                "outcome": r[5],
                "reward": r[6],
                "timestamp": r[7],
                "value": r[8],
                "metadata": json.loads(r[9]) if r[9] else {},
                "embedding": json.loads(r[10]) if r[10] else [],
            }
            for r in rows
        ]

    def forget(self, key: str) -> bool:
        c = self._conn.execute("DELETE FROM episodes WHERE event_id = ?", (key,))
        self._conn.commit()
        return c.rowcount > 0

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM episodes").fetchone()
        return row[0] if row else 0

    def clear(self) -> None:
        self._conn.execute("DELETE FROM episodes")
        self._conn.commit()
