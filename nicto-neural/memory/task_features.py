"""Task feature memory — task feature vectors for routing."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .base import MemoryEntry, MemoryStore


class TaskFeatureMemory(MemoryStore):
    """Stores task feature vectors for brain routing decisions."""

    def __init__(self, db_path):
        path = Path(db_path).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path / "task_features.db"))
        self._init_schema()

    def _init_schema(self):
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS task_features (
                id TEXT PRIMARY KEY,
                content TEXT,
                metadata TEXT,
                timestamp TEXT,
                importance REAL DEFAULT 0.5
            )
        """)
        self._db.commit()

    def store(self, entry: MemoryEntry) -> str:
        self._db.execute(
            """INSERT OR REPLACE INTO task_features
            (id, content, metadata, timestamp, importance)
            VALUES (?, ?, ?, ?, ?)""",
            (
                entry.id,
                json.dumps(entry.content) if entry.content is not None else "null",
                json.dumps(entry.metadata),
                entry.timestamp.isoformat(),
                entry.importance,
            ),
        )
        self._db.commit()
        return entry.id

    def recall(self, query: str, limit: int = 10) -> list:
        cursor = self._db.execute(
            """SELECT id, content, metadata, timestamp, importance
            FROM task_features ORDER BY timestamp DESC LIMIT ?""",
            (limit,),
        )
        results = []
        for row in cursor.fetchall():
            results.append(MemoryEntry(
                id=row[0],
                content=json.loads(row[1]),
                metadata=json.loads(row[2]),
                timestamp=datetime.fromisoformat(row[3]),
                importance=row[4],
            ))
        return results

    def get(self, id: str) -> Optional[MemoryEntry]:
        cursor = self._db.execute(
            "SELECT id, content, metadata, timestamp, importance FROM task_features WHERE id=?",
            (id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return MemoryEntry(
            id=row[0],
            content=json.loads(row[1]),
            metadata=json.loads(row[2]),
            timestamp=datetime.fromisoformat(row[3]),
            importance=row[4],
        )

    def delete(self, id: str) -> bool:
        self._db.execute("DELETE FROM task_features WHERE id=?", (id,))
        self._db.commit()
        return True

    def count(self) -> int:
        return self._db.execute("SELECT COUNT(*) FROM task_features").fetchone()[0]
