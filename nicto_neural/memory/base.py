from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import time
import json


class MemoryEntry:
    def __init__(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict] = None,
        timestamp: Optional[float] = None,
        embedding: Optional[List[float]] = None,
    ):
        self.key = key
        self.value = value
        self.metadata = metadata or {}
        self.timestamp = timestamp or time.time()
        self.embedding = embedding or []

    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "value": self.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "embedding": self.embedding,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "MemoryEntry":
        return cls(
            key=d["key"],
            value=d["value"],
            metadata=d.get("metadata", {}),
            timestamp=d.get("timestamp", time.time()),
            embedding=d.get("embedding", []),
        )


class StoreMetadata:
    def __init__(
        self,
        store_type: str,
        version: str = "1.0.0",
        created_at: Optional[float] = None,
        entry_count: int = 0,
        last_consolidated: Optional[float] = None,
    ):
        self.store_type = store_type
        self.version = version
        self.created_at = created_at or time.time()
        self.entry_count = entry_count
        self.last_consolidated = last_consolidated or 0.0

    def to_dict(self) -> Dict:
        return {
            "store_type": self.store_type,
            "version": self.version,
            "created_at": self.created_at,
            "entry_count": self.entry_count,
            "last_consolidated": self.last_consolidated,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "StoreMetadata":
        return cls(
            store_type=d.get("store_type", "unknown"),
            version=d.get("version", "1.0.0"),
            created_at=d.get("created_at", time.time()),
            entry_count=d.get("entry_count", 0),
            last_consolidated=d.get("last_consolidated", 0.0),
        )


class MemoryStore(ABC):
    def __init__(self, store_name: str, base_path: Optional[str] = None):
        self.store_name = store_name
        self._metadata = StoreMetadata(store_type=self.__class__.__name__)
        db_path = os.path.join(base_path or self._default_path(), f"{store_name}.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_db()

    def _default_path(self) -> str:
        return os.path.expanduser("~/.nicto/neural/memory")

    @abstractmethod
    def _init_db(self) -> None:
        ...

    @abstractmethod
    def store(self, key: str, value: Any, metadata: Optional[Dict] = None) -> str:
        ...

    @abstractmethod
    def query(self, query_text: str, limit: int = 10) -> List[Dict]:
        ...

    @abstractmethod
    def recall(self, key: str) -> Optional[Any]:
        ...

    @abstractmethod
    def forget(self, key: str) -> bool:
        ...

    @abstractmethod
    def count(self) -> int:
        ...

    @abstractmethod
    def clear(self) -> None:
        ...

    def consolidate(self) -> None:
        self._conn.execute("VACUUM")
        self._metadata.last_consolidated = time.time()

    def close(self) -> None:
        self._conn.close()

    def __del__(self):
        try:
            self._conn.close()
        except Exception:
            pass

    @property
    def metadata(self) -> StoreMetadata:
        self._metadata.entry_count = self.count()
        return self._metadata

    def size_bytes(self) -> int:
        try:
            return os.path.getsize(self._db_path)
        except OSError:
            return 0


import os
import sqlite3
