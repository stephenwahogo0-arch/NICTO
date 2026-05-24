import os
import json
import time
import logging
from typing import Optional
from uuid import uuid4
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, Column, String, Text, Float, Integer, DateTime, MetaData, Table
from sqlalchemy.orm import sessionmaker, declarative_base

from kyros.config.settings import MemoryConfig

logger = logging.getLogger(__name__)

Base = declarative_base()


class MemoryEntry(Base):
    __tablename__ = "memory_entries"
    id = Column(String, primary_key=True)
    content = Column(Text, nullable=False)
    source = Column(String, default="user")
    created_at = Column(Float, default=time.time)
    embedding_id = Column(String, nullable=True)


class MemorySystem:
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        base_dir = Path(os.path.join(str(Path.home()), ".nikto", "memory"))
        base_dir.mkdir(parents=True, exist_ok=True)
        db_path = base_dir / "memory.db"
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self._chroma_client = None
        self._chroma_collection = None

    def _get_chroma(self):
        if self._chroma_client is None:
            try:
                import chromadb
                base_dir = Path(os.path.join(str(Path.home()), ".nikto", "memory"))
                self._chroma_client = chromadb.PersistentClient(path=str(base_dir / "chroma"))
                self._chroma_collection = self._chroma_client.get_or_create_collection("nikto_memory")
            except Exception as e:
                logger.warning(f"ChromaDB init failed: {e}")
        return self._chroma_collection

    async def store(self, content: str, source: str = "user") -> dict:
        entry_id = str(uuid4())[:12]
        entry = MemoryEntry(id=entry_id, content=content, source=source, created_at=time.time())
        self.session.add(entry)
        self.session.commit()
        collection = self._get_chroma()
        if collection:
            try:
                collection.add(documents=[content], ids=[entry_id], metadatas=[{"source": source, "created_at": time.time()}])
            except Exception as e:
                logger.warning(f"ChromaDB store failed: {e}")
        return {"id": entry_id, "content": content, "source": source, "stored": True}

    async def get_context(self, query: str, limit: int = 5) -> str:
        collection = self._get_chroma()
        if collection:
            try:
                results = collection.query(query_texts=[query], n_results=limit)
                if results and results.get("documents"):
                    return "\n".join(results["documents"][0])
            except Exception as e:
                logger.warning(f"ChromaDB query failed: {e}")
        entries = self.session.query(MemoryEntry).order_by(MemoryEntry.created_at.desc()).limit(limit).all()
        return "\n".join(e.content for e in entries)

    async def get_stats(self) -> dict:
        count = self.session.query(MemoryEntry).count()
        return {"total_entries": count, "vector_store": self.config.vector_store}

    def close(self):
        self.session.close()
