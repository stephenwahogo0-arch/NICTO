from typing import Any, Dict, List, Optional


class MemoryAPI:
    def __init__(self, memory_manager=None):
        self._memory = memory_manager

    def store(self, key: str, value: Any, store_type: str = "episodic", metadata: Dict = None) -> Dict:
        if self._memory is None:
            return {"error": "MemoryManager not initialized"}
        result = self._memory.store(key, value, store_type, metadata or {})
        return {"key": key, "store_type": store_type, "result": result}

    def recall(self, key: str, store_type: Optional[str] = None) -> Dict:
        if self._memory is None:
            return {"error": "MemoryManager not initialized"}
        result = self._memory.recall(key, store_type)
        return {"key": key, "found": result is not None, "data": result}

    def search(self, query: str, store_types: List[str] = None, limit: int = 10) -> Dict:
        if self._memory is None:
            return {"error": "MemoryManager not initialized"}
        results = self._memory.query(query, store_types, limit)
        return {"query": query, "count": len(results), "results": results}

    def consolidate(self) -> Dict:
        if self._memory is None:
            return {"error": "MemoryManager not initialized"}
        self._memory.consolidate_all()
        return {"status": "consolidated"}

    def set_memory_manager(self, memory_manager):
        self._memory = memory_manager