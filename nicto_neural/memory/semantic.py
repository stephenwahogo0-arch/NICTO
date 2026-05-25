from .base import MemoryStore, MemoryEntry
from typing import Any, Dict, List, Optional, Tuple
import json
import time
import math
import os


class SemanticMemory(MemoryStore):
    def __init__(self, store_name: str = "semantic", base_path: Optional[str] = None):
        super().__init__(store_name, base_path)

    def _init_db(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                fact_id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                timestamp REAL NOT NULL,
                metadata TEXT DEFAULT '{}',
                embedding TEXT DEFAULT '[]'
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_fact_subject
            ON facts(subject)
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_fact_predicate
            ON facts(predicate)
        """)
        self._conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_spo
            ON facts(subject, predicate, object)
        """)
        self._conn.commit()

    def store_fact(
        self,
        subject: str,
        predicate: str,
        object: str,
        confidence: float = 1.0,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        fact_id = f"fact_{int(time.time() * 1e6)}"
        ts = time.time()
        emb = json.dumps(embedding or [])
        md = json.dumps(metadata or {})
        self._conn.execute(
            """
            INSERT OR REPLACE INTO facts
            (fact_id, subject, predicate, object, confidence, timestamp, metadata, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (fact_id, subject, predicate, object, confidence, ts, md, emb),
        )
        self._conn.commit()
        return fact_id

    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        md = metadata or {}
        if isinstance(value, dict) and "subject" in value and "predicate" in value:
            return self.store_fact(
                subject=value["subject"],
                predicate=value["predicate"],
                object=value.get("object", ""),
                confidence=value.get("confidence", 1.0),
                embedding=md.get("embedding"),
                metadata=md,
            )
        return self.store_fact(
            subject=key,
            predicate=md.get("predicate", "is"),
            object=json.dumps(value) if not isinstance(value, str) else value,
            confidence=md.get("confidence", 1.0),
            embedding=md.get("embedding"),
            metadata=md,
        )

    def query_facts(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        conditions = []
        params = []
        if subject:
            conditions.append("subject = ?")
            params.append(subject)
        if predicate:
            conditions.append("predicate = ?")
            params.append(predicate)
        where = " AND ".join(conditions) if conditions else "1=1"
        rows = self._conn.execute(
            f"SELECT fact_id, subject, predicate, object, confidence, timestamp, metadata, embedding FROM facts WHERE {where} ORDER BY confidence DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        return [
            {
                "fact_id": r[0],
                "subject": r[1],
                "predicate": r[2],
                "object": r[3],
                "confidence": r[4],
                "timestamp": r[5],
                "metadata": json.loads(r[6]) if r[6] else {},
                "embedding": json.loads(r[7]) if r[7] else [],
            }
            for r in rows
        ]

    def query(self, query_text: str = "", limit: int = 10) -> List[Dict]:
        return self.query_facts(subject=query_text if query_text else None, limit=limit)

    def similarity_search(
        self, vector: List[float], limit: int = 5
    ) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT fact_id, subject, predicate, object, confidence, timestamp, metadata, embedding FROM facts ORDER BY timestamp DESC LIMIT 1000"
        ).fetchall()
        scored = []
        for r in rows:
            emb = json.loads(r[7]) if r[7] else []
            if emb:
                sim = sum(a * b for a, b in zip(vector, emb))
                na = math.sqrt(sum(x * x for x in vector))
                nb = math.sqrt(sum(y * y for y in emb))
                if na > 0 and nb > 0:
                    sim /= na * nb
                scored.append((sim, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for _, r in scored[:limit]:
            results.append({
                "fact_id": r[0],
                "subject": r[1],
                "predicate": r[2],
                "object": r[3],
                "confidence": r[4],
                "timestamp": r[5],
                "metadata": json.loads(r[6]) if r[6] else {},
                "embedding": json.loads(r[7]) if r[7] else [],
                "similarity": _,
            })
        return results

    def recall(self, key: str) -> Optional[Any]:
        facts = self.query_facts(subject=key, limit=1)
        if facts:
            return facts[0]
        row = self._conn.execute(
            "SELECT object FROM facts WHERE fact_id = ?", (key,)
        ).fetchone()
        if row:
            try:
                return json.loads(row[0])
            except (json.JSONDecodeError, TypeError):
                return row[0]
        return None

    def forget(self, key: str) -> bool:
        c = self._conn.execute("DELETE FROM facts WHERE fact_id = ?", (key,))
        self._conn.commit()
        return c.rowcount > 0

    def count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) FROM facts").fetchone()
        return row[0] if row else 0

    def clear(self) -> None:
        self._conn.execute("DELETE FROM facts")
        self._conn.commit()
