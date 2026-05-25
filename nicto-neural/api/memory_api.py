"""Memory API — MemoryManager public interface."""


class MemoryAPI:
    """Public API for memory operations."""

    def __init__(self, memory_manager):
        self.memory = memory_manager

    def store(self, content, metadata: dict = None) -> str:
        return self.memory.store_episode(content, metadata)

    def recall(self, query: str = "recent", limit: int = 10) -> list:
        return [
            {
                "id": e.id,
                "content": e.content,
                "importance": e.importance,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in self.memory.episodic.recall(query, limit)
        ]

    def search_knowledge(self, query: str, limit: int = 10) -> list:
        return [
            {
                "id": e.id,
                "content": e.content,
                "importance": e.importance,
            }
            for e in self.memory.semantic.recall(query, limit)
        ]

    def get_stats(self) -> dict:
        return self.memory.total_memories()

    def consolidate(self) -> None:
        self.memory.consolidate()
