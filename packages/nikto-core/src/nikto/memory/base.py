import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from nikto.config.settings import MemoryConfig


class MemorySystem:
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.db_path = Path(config.sqlite_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

        self._vector_enabled = False
        try:
            import chromadb
            self.chroma_path = str(Path(config.chroma_path).expanduser())
            self.chroma = chromadb.PersistentClient(path=self.chroma_path)
            try:
                self.collection = self.chroma.get_collection("nikto_memory")
            except Exception:
                self.collection = self.chroma.create_collection("nikto_memory")
            self._vector_enabled = True
        except ImportError:
            self._vector_enabled = False

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                session_id TEXT,
                type TEXT,
                content TEXT,
                metadata TEXT,
                created_at REAL,
                ttl REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tool_calls (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                tool_name TEXT,
                arguments TEXT,
                result TEXT,
                created_at REAL
            )
        """)
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
            USING fts5(content, content=memories, content_rowid=rowid)
        """)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.commit()
        conn.close()

    async def store(self, task: str, result: str, metadata: Optional[dict] = None):
        mem_id = str(uuid.uuid4())
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO memories (id, type, content, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (mem_id, "task_result", f"Task: {task}\nResult: {result[:2000]}",
             json.dumps(metadata or {}), time.time()),
        )
        conn.commit()
        conn.close()

        if self._vector_enabled:
            try:
                self.collection.add(
                    ids=[mem_id],
                    documents=[f"Task: {task}\nResult: {result}"],
                    metadatas=[{"type": "task_result", "timestamp": time.time()}],
                )
            except Exception:
                pass

    async def store_tool_call(self, tool_name: str, arguments: dict, result: str):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO tool_calls (id, tool_name, arguments, result, created_at) VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), tool_name, json.dumps(arguments), result[:2000], time.time()),
        )
        conn.commit()
        conn.close()

    async def get_context(self, task: str) -> Optional[str]:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute(
            "SELECT content FROM memories ORDER BY created_at DESC LIMIT 10"
        )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        context = "## Recent Memory\n"
        for i, (content,) in enumerate(rows, 1):
            context += f"{i}. {content[:500]}\n"
        return context

    async def search(self, query: str, limit: int = 5) -> list[dict]:
        results = []

        if self._vector_enabled:
            try:
                vector_results = self.collection.query(
                    query_texts=[query], n_results=limit
                )
                for i, doc in enumerate(vector_results["documents"][0]):
                    results.append({
                        "content": doc,
                        "score": vector_results["distances"][0][i] if vector_results.get("distances") else 0,
                        "type": "vector",
                    })
            except Exception:
                pass

        if not results:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.execute(
                    "SELECT content FROM memories_fts WHERE content MATCH ? LIMIT ?",
                    (query, limit),
                )
                for row in cursor:
                    results.append({"content": row[0], "type": "fts"})
            except Exception:
                pass
            cursor = conn.execute(
                "SELECT content FROM memories ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            for row in cursor:
                results.append({"content": row[0], "type": "recent"})
            conn.close()

        return results[:limit]

    async def recent(self, limit: int = 10) -> list[dict]:
        results = []
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.execute(
                "SELECT content, type, created_at FROM memories ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            for row in cursor:
                results.append({"content": row[0], "type": row[1], "created_at": row[2]})
        except Exception:
            pass
        conn.close()
        return results

    async def get_stats(self) -> dict:
        conn = sqlite3.connect(str(self.db_path))
        mem_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        tool_count = conn.execute("SELECT COUNT(*) FROM tool_calls").fetchone()[0]
        conn.close()
        return {"memories": mem_count, "tool_calls": tool_count, "vector_enabled": self._vector_enabled}
