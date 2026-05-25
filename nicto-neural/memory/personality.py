from .base import MemoryStore, MemoryEntry
from typing import Any, Dict, List, Optional, Tuple
import json
import time
import os


PERSONALITY_TRAITS = [
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
    "risk_tolerance",
    "creativity",
    "curiosity",
    "assertiveness",
    "empathy",
]


class PersonalityMemory(MemoryStore):
    def __init__(self, store_name: str = "personality", base_path: Optional[str] = None):
        super().__init__(store_name, base_path)

    def _init_db(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS traits (
                trait_name TEXT PRIMARY KEY,
                value REAL NOT NULL DEFAULT 0.5,
                confidence REAL NOT NULL DEFAULT 0.5,
                last_updated REAL NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        self._conn.commit()
        self._init_defaults()

    def _init_defaults(self) -> None:
        ts = time.time()
        for trait in PERSONALITY_TRAITS:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO traits (trait_name, value, confidence, last_updated, metadata)
                VALUES (?, 0.5, 0.5, ?, '{}')
                """,
                (trait, ts),
            )
        self._conn.commit()

    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        md = metadata or {}
        if isinstance(value, dict):
            val = value.get("value", 0.5)
            conf = value.get("confidence", md.get("confidence", 0.5))
        else:
            val = float(value)
            conf = md.get("confidence", 0.5)
        return self.set_trait(key, val, conf, md)

    def set_trait(
        self,
        name: str,
        value: float,
        confidence: float = 0.5,
        metadata: Optional[Dict] = None,
    ) -> str:
        value = min(max(value, 0.0), 1.0)
        confidence = min(max(confidence, 0.0), 1.0)
        self._conn.execute(
            """
            INSERT OR REPLACE INTO traits (trait_name, value, confidence, last_updated, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, value, confidence, time.time(), json.dumps(metadata or {})),
        )
        self._conn.commit()
        return name

    def get_trait(self, name: str) -> Optional[Dict]:
        row = self._conn.execute(
            "SELECT trait_name, value, confidence, last_updated, metadata FROM traits WHERE trait_name = ?",
            (name,),
        ).fetchone()
        if row:
            return {
                "trait_name": row[0],
                "value": row[1],
                "confidence": row[2],
                "last_updated": row[3],
                "metadata": json.loads(row[4]) if row[4] else {},
            }
        return None

    def all_traits(self) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT trait_name, value, confidence, last_updated, metadata FROM traits ORDER BY trait_name"
        ).fetchall()
        return [
            {
                "trait_name": r[0],
                "value": r[1],
                "confidence": r[2],
                "last_updated": r[3],
                "metadata": json.loads(r[4]) if r[4] else {},
            }
            for r in rows
        ]

    def profile_vector(self) -> List[float]:
        rows = self._conn.execute(
            "SELECT trait_name, value FROM traits ORDER BY trait_name"
        ).fetchall()
        trait_map = {r[0]: r[1] for r in rows}
        return [trait_map.get(t, 0.5) for t in PERSONALITY_TRAITS]

    def query(self, query_text: str = "", limit: int = 10) -> List[Dict]:
        if query_text:
            row = self.get_trait(query_text)
            return [row] if row else []
        return self.all_traits()[:limit]

    def recall(self, key: str) -> Optional[Any]:
        return self.get_trait(key)

    def forget(self, key: str) -> bool:
        if key in PERSONALITY_TRAITS:
            return False
        c = self._conn.execute("DELETE FROM traits WHERE trait_name = ?", (key,))
        self._conn.commit()
        return c.rowcount > 0

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM traits").fetchone()
        return row[0] if row else 0

    def clear(self) -> None:
        self._conn.execute("DELETE FROM traits")
        self._conn.commit()
        self._init_defaults()
