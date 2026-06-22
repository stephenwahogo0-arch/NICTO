from .base import MemoryStore, MemoryEntry
from typing import Any, Dict, List, Optional, Tuple
import json
import time
import math
import os
import random


class ExperienceMemory(MemoryStore):
    def __init__(self, store_name: str = "experience", base_path: Optional[str] = None):
        super().__init__(store_name, base_path)
        self._max_entries = 100000

    def set_max_entries(self, n: int) -> None:
        self._max_entries = n

    def _init_db(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS experiences (
                experience_id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                action INTEGER NOT NULL,
                reward REAL NOT NULL,
                next_state TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                priority REAL DEFAULT 1.0,
                timestamp REAL NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_exp_priority
            ON experiences(priority)
        """)
        self._conn.commit()

    def add_experience(
        self,
        state: List[float],
        action: int,
        reward: float,
        next_state: List[float],
        done: bool = False,
        priority: float = 1.0,
        metadata: Optional[Dict] = None,
    ) -> str:
        exp_id = f"exp_{int(time.time() * 1e6)}_{random.randint(0, 99999)}"
        self._conn.execute(
            """
            INSERT INTO experiences
            (experience_id, state, action, reward, next_state, done, priority, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                exp_id,
                json.dumps(state),
                action,
                reward,
                json.dumps(next_state),
                1 if done else 0,
                priority,
                time.time(),
                json.dumps(metadata or {}),
            ),
        )
        self._conn.commit()
        if self.count() > self._max_entries:
            self._evict_lru()
        return exp_id

    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        md = metadata or {}
        if isinstance(value, dict):
            return self.add_experience(
                state=value.get("state", md.get("state", [])),
                action=value.get("action", md.get("action", 0)),
                reward=value.get("reward", md.get("reward", 0.0)),
                next_state=value.get("next_state", md.get("next_state", [])),
                done=value.get("done", md.get("done", False)),
                priority=value.get("priority", md.get("priority", 1.0)),
                metadata=md,
            )
        return self.add_experience(
            state=md.get("state", []),
            action=int(value) if isinstance(value, (int, float)) else 0,
            reward=md.get("reward", 0.0),
            next_state=md.get("next_state", []),
            done=md.get("done", False),
            priority=md.get("priority", 1.0),
            metadata=md,
        )

    def sample(self, batch_size: int = 32, alpha: float = 0.6) -> List[Dict]:
        total = self.count()
        if total == 0:
            return []
        batch_size = min(batch_size, total)
        rows = self._conn.execute(
            "SELECT experience_id, state, action, reward, next_state, done, priority, timestamp FROM experiences ORDER BY priority DESC"
        ).fetchall()
        if alpha <= 0:
            sampled = random.sample(rows, batch_size)
        else:
            priorities = [r[6] for r in rows]
            p_min = min(priorities) if priorities else 1.0
            probs = [(p - p_min + 1e-6) ** alpha for p in priorities]
            total_p = sum(probs)
            probs = [p / total_p for p in probs]
            indices = list(range(len(rows)))
            chosen = random.choices(indices, weights=probs, k=batch_size)
            sampled = [rows[i] for i in chosen]
        return [
            {
                "experience_id": r[0],
                "state": json.loads(r[1]),
                "action": r[2],
                "reward": r[3],
                "next_state": json.loads(r[4]),
                "done": bool(r[5]),
                "priority": r[6],
                "timestamp": r[7],
            }
            for r in sampled
        ]

    def update_priorities(self, indices: List[int], priorities: List[float]) -> None:
        for idx, prio in zip(indices, priorities):
            row = self._conn.execute(
                "SELECT experience_id FROM experiences ORDER BY priority DESC LIMIT 1 OFFSET ?",
                (idx,),
            ).fetchone()
            if row:
                self._conn.execute(
                    "UPDATE experiences SET priority = ? WHERE experience_id = ?",
                    (prio, row[0]),
                )
        self._conn.commit()

    def _evict_lru(self) -> None:
        self._conn.execute(
            "DELETE FROM experiences WHERE experience_id IN (SELECT experience_id FROM experiences ORDER BY timestamp ASC LIMIT ?)",
            (max(1, self._max_entries // 100),),
        )
        self._conn.commit()

    def query(self, query_text: str = "", limit: int = 10) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT experience_id, state, action, reward, next_state, done, priority, timestamp, metadata FROM experiences ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {
                "experience_id": r[0],
                "state": json.loads(r[1]),
                "action": r[2],
                "reward": r[3],
                "next_state": json.loads(r[4]),
                "done": bool(r[5]),
                "priority": r[6],
                "timestamp": r[7],
                "metadata": json.loads(r[8]) if r[8] else {},
            }
            for r in rows
        ]

    def recall(self, key: str) -> Optional[Any]:
        row = self._conn.execute(
            "SELECT experience_id, state, action, reward, next_state, done, priority, timestamp, metadata FROM experiences WHERE experience_id = ?",
            (key,),
        ).fetchone()
        if row:
            return {
                "experience_id": row[0],
                "state": json.loads(row[1]),
                "action": row[2],
                "reward": row[3],
                "next_state": json.loads(row[4]),
                "done": bool(row[5]),
                "priority": row[6],
                "timestamp": row[7],
                "metadata": json.loads(row[8]) if row[8] else {},
            }
        return None

    def forget(self, key: str) -> bool:
        c = self._conn.execute("DELETE FROM experiences WHERE experience_id = ?", (key,))
        self._conn.commit()
        return c.rowcount > 0

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM experiences").fetchone()
        return row[0] if row else 0

    def clear(self) -> None:
        self._conn.execute("DELETE FROM experiences")
        self._conn.commit()
