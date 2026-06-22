from .base import MemoryStore, MemoryEntry
from typing import Any, Dict, List, Optional, Tuple
import json
import time
import os


class SkillMemory(MemoryStore):
    def __init__(self, store_name: str = "skills", base_path: Optional[str] = None):
        super().__init__(store_name, base_path)

    def _init_db(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                skill_name TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                mastery_level REAL DEFAULT 0.0,
                examples_attempted INTEGER DEFAULT 0,
                examples_succeeded INTEGER DEFAULT 0,
                prototype_vector TEXT DEFAULT '[]',
                last_used REAL DEFAULT 0.0,
                metadata TEXT DEFAULT '{}'
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_skills_domain
            ON skills(domain)
        """)
        self._conn.commit()

    def register_skill(
        self,
        name: str,
        domain: str,
        prototype_vector: Optional[List[float]] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        self._conn.execute(
            """
            INSERT OR REPLACE INTO skills
            (skill_name, domain, mastery_level, examples_attempted, examples_succeeded, prototype_vector, last_used, metadata)
            VALUES (?, ?, 0.0, 0, 0, ?, ?, ?)
            """,
            (name, domain, json.dumps(prototype_vector or []), time.time(), json.dumps(metadata or {})),
        )
        self._conn.commit()
        return name

    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        md = metadata or {}
        domain = md.get("domain", "general")
        proto = md.get("prototype_vector", [])
        return self.register_skill(key, domain, proto, md)

    def update_mastery(self, name: str, succeeded: bool) -> None:
        row = self._conn.execute(
            "SELECT examples_attempted, examples_succeeded, mastery_level FROM skills WHERE skill_name = ?",
            (name,),
        ).fetchone()
        if not row:
            return
        attempted = row[0] + 1
        succeeded_count = row[1] + (1 if succeeded else 0)
        mastery = succeeded_count / max(attempted, 1)
        mastery = min(max(mastery, 0.0), 1.0)
        self._conn.execute(
            "UPDATE skills SET mastery_level = ?, examples_attempted = ?, examples_succeeded = ?, last_used = ? WHERE skill_name = ?",
            (mastery, attempted, succeeded_count, time.time(), name),
        )
        self._conn.commit()

    def top_skills(self, domain: Optional[str] = None, limit: int = 5) -> List[Dict]:
        if domain:
            rows = self._conn.execute(
                "SELECT skill_name, domain, mastery_level, examples_attempted, examples_succeeded, prototype_vector, last_used, metadata FROM skills WHERE domain = ? ORDER BY mastery_level DESC LIMIT ?",
                (domain, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT skill_name, domain, mastery_level, examples_attempted, examples_succeeded, prototype_vector, last_used, metadata FROM skills ORDER BY mastery_level DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "skill_name": r[0],
                "domain": r[1],
                "mastery_level": r[2],
                "examples_attempted": r[3],
                "examples_succeeded": r[4],
                "prototype_vector": json.loads(r[5]) if r[5] else [],
                "last_used": r[6],
                "metadata": json.loads(r[7]) if r[7] else {},
            }
            for r in rows
        ]

    def get_prototype(self, name: str) -> Optional[List[float]]:
        row = self._conn.execute(
            "SELECT prototype_vector FROM skills WHERE skill_name = ?", (name,)
        ).fetchone()
        if row:
            return json.loads(row[0]) if row[0] else []
        return None

    def query(self, query_text: str = "", limit: int = 10) -> List[Dict]:
        return self.top_skills(domain=query_text if query_text else None, limit=limit)

    def recall(self, key: str) -> Optional[Any]:
        row = self._conn.execute(
            "SELECT skill_name, domain, mastery_level, examples_attempted, examples_succeeded, prototype_vector, last_used, metadata FROM skills WHERE skill_name = ?",
            (key,),
        ).fetchone()
        if row:
            return {
                "skill_name": row[0],
                "domain": row[1],
                "mastery_level": row[2],
                "examples_attempted": row[3],
                "examples_succeeded": row[4],
                "prototype_vector": json.loads(row[5]) if row[5] else [],
                "last_used": row[6],
                "metadata": json.loads(row[7]) if row[7] else {},
            }
        return None

    def forget(self, key: str) -> bool:
        c = self._conn.execute("DELETE FROM skills WHERE skill_name = ?", (key,))
        self._conn.commit()
        return c.rowcount > 0

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM skills").fetchone()
        return row[0] if row else 0

    def clear(self) -> None:
        self._conn.execute("DELETE FROM skills")
        self._conn.commit()
