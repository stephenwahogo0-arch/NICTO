from .base import MemoryStore, MemoryEntry
from typing import Any, Dict, List, Optional, Tuple
import json
import time
import os


class ReflectionMemory(MemoryStore):
    def __init__(self, store_name: str = "reflection", base_path: Optional[str] = None):
        super().__init__(store_name, base_path)

    def _init_db(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS reflections (
                reflection_id TEXT PRIMARY KEY,
                task_id TEXT DEFAULT '',
                brain TEXT DEFAULT '',
                domain TEXT DEFAULT '',
                was_correct INTEGER DEFAULT 1,
                confidence REAL DEFAULT 0.0,
                missing_knowledge TEXT DEFAULT '',
                needed_tool TEXT DEFAULT '',
                improvement TEXT DEFAULT '',
                score REAL DEFAULT 0.0,
                timestamp REAL NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ref_brain
            ON reflections(brain)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ref_domain
            ON reflections(domain)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_ref_score
            ON reflections(score)
        """)
        self._conn.commit()

    def store_reflection(self, record: Dict) -> str:
        ref_id = record.get("reflection_id", f"ref_{int(time.time() * 1e6)}")
        str_or_empty = lambda v: str(v) if v else ""
        self._conn.execute(
            """
            INSERT OR REPLACE INTO reflections
            (reflection_id, task_id, brain, domain, was_correct, confidence, missing_knowledge, needed_tool, improvement, score, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ref_id,
                str_or_empty(record.get("task_id", "")),
                str_or_empty(record.get("brain", "")),
                str_or_empty(record.get("domain", "")),
                1 if record.get("was_correct", True) else 0,
                record.get("confidence", 0.0),
                str_or_empty(record.get("missing_knowledge", "")),
                str_or_empty(record.get("needed_tool", "")),
                str_or_empty(record.get("improvement", record.get("improvement_suggestion", ""))),
                record.get("score", 0.0),
                record.get("timestamp", time.time()),
                json.dumps(record.get("metadata", {})),
            ),
        )
        self._conn.commit()
        return ref_id

    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        md = metadata or {}
        if isinstance(value, dict):
            record = value
            record["reflection_id"] = key or record.get("reflection_id")
            record.update(md)
        else:
            record = {"reflection_id": key, "improvement": str(value), **md}
        return self.store_reflection(record)

    def recent_reflections(self, n: int = 10) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT reflection_id, task_id, brain, domain, was_correct, confidence, missing_knowledge, needed_tool, improvement, score, timestamp, metadata FROM reflections ORDER BY timestamp DESC LIMIT ?",
            (n,),
        ).fetchall()
        return [
            {
                "reflection_id": r[0],
                "task_id": r[1],
                "brain": r[2],
                "domain": r[3],
                "was_correct": bool(r[4]),
                "confidence": r[5],
                "missing_knowledge": r[6],
                "needed_tool": r[7],
                "improvement": r[8],
                "score": r[9],
                "timestamp": r[10],
                "metadata": json.loads(r[11]) if r[11] else {},
            }
            for r in rows
        ]

    def reflections_by_brain(self, brain: str) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT reflection_id, task_id, brain, domain, was_correct, confidence, missing_knowledge, needed_tool, improvement, score, timestamp, metadata FROM reflections WHERE brain = ? ORDER BY timestamp DESC",
            (brain,),
        ).fetchall()
        return [
            {
                "reflection_id": r[0],
                "task_id": r[1],
                "brain": r[2],
                "domain": r[3],
                "was_correct": bool(r[4]),
                "confidence": r[5],
                "missing_knowledge": r[6],
                "needed_tool": r[7],
                "improvement": r[8],
                "score": r[9],
                "timestamp": r[10],
                "metadata": json.loads(r[11]) if r[11] else {},
            }
            for r in rows
        ]

    def low_score_reflections(self, threshold: float = 0.5) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT reflection_id, task_id, brain, domain, was_correct, confidence, missing_knowledge, needed_tool, improvement, score, timestamp, metadata FROM reflections WHERE score < ? ORDER BY score ASC",
            (threshold,),
        ).fetchall()
        return [
            {
                "reflection_id": r[0],
                "task_id": r[1],
                "brain": r[2],
                "domain": r[3],
                "was_correct": bool(r[4]),
                "confidence": r[5],
                "missing_knowledge": r[6],
                "needed_tool": r[7],
                "improvement": r[8],
                "score": r[9],
                "timestamp": r[10],
                "metadata": json.loads(r[11]) if r[11] else {},
            }
            for r in rows
        ]

    def improvement_suggestions(self, domain: str) -> List[str]:
        rows = self._conn.execute(
            "SELECT improvement, missing_knowledge, needed_tool FROM reflections WHERE domain = ? AND score < 0.7 ORDER BY score ASC LIMIT 20",
            (domain,),
        ).fetchall()
        suggestions = []
        for r in rows:
            if r[0]:
                suggestions.append(r[0])
            if r[1]:
                suggestions.append(f"Study: {r[1]}")
            if r[2]:
                suggestions.append(f"Tool needed: {r[2]}")
        return suggestions

    def query(self, query_text: str = "", limit: int = 10) -> List[Dict]:
        if query_text:
            like = f"%{query_text}%"
            rows = self._conn.execute(
                "SELECT reflection_id, task_id, brain, domain, was_correct, confidence, missing_knowledge, needed_tool, improvement, score, timestamp, metadata FROM reflections WHERE domain LIKE ? OR brain LIKE ? OR improvement LIKE ? ORDER BY timestamp DESC LIMIT ?",
                (like, like, like, limit),
            ).fetchall()
        else:
            return self.recent_reflections(limit)
        return [
            {
                "reflection_id": r[0],
                "task_id": r[1],
                "brain": r[2],
                "domain": r[3],
                "was_correct": bool(r[4]),
                "confidence": r[5],
                "missing_knowledge": r[6],
                "needed_tool": r[7],
                "improvement": r[8],
                "score": r[9],
                "timestamp": r[10],
                "metadata": json.loads(r[11]) if r[11] else {},
            }
            for r in rows
        ]

    def recall(self, key: str) -> Optional[Any]:
        row = self._conn.execute(
            "SELECT reflection_id, task_id, brain, domain, was_correct, confidence, missing_knowledge, needed_tool, improvement, score, timestamp, metadata FROM reflections WHERE reflection_id = ?",
            (key,),
        ).fetchone()
        if row:
            return {
                "reflection_id": row[0],
                "task_id": row[1],
                "brain": row[2],
                "domain": row[3],
                "was_correct": bool(row[4]),
                "confidence": row[5],
                "missing_knowledge": row[6],
                "needed_tool": row[7],
                "improvement": row[8],
                "score": row[9],
                "timestamp": row[10],
                "metadata": json.loads(row[11]) if row[11] else {},
            }
        return None

    def forget(self, key: str) -> bool:
        c = self._conn.execute("DELETE FROM reflections WHERE reflection_id = ?", (key,))
        self._conn.commit()
        return c.rowcount > 0

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM reflections").fetchone()
        return row[0] if row else 0

    def clear(self) -> None:
        self._conn.execute("DELETE FROM reflections")
        self._conn.commit()
