"""Abstract base class for all memory stores."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4


@dataclass
class MemoryEntry:
    id: str = field(default_factory=lambda: str(uuid4())[:16])
    content: Any = None
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    importance: float = 0.5
    embedding: Optional[list] = None


class MemoryStore(ABC):
    @abstractmethod
    def store(self, entry: MemoryEntry) -> str: ...

    @abstractmethod
    def recall(self, query: str, limit: int = 10) -> list: ...

    @abstractmethod
    def get(self, id: str) -> Optional[MemoryEntry]: ...

    @abstractmethod
    def delete(self, id: str) -> bool: ...

    @abstractmethod
    def count(self) -> int: ...
