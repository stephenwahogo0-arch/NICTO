"""
Evolution Engine for NIKTO.

Tracks evolutionary progress across cycles and milestones.
"""

from typing import Any


class EvolutionProtocol:
    """Tracks evolution cycles and computes the current level.

    The ``.level`` property starts at 1 and increments when
    ``evolution_count`` crosses milestones (10, 50, 100, 500).
    """

    MILESTONES: list[int] = [10, 50, 100, 500]

    def __init__(self) -> None:
        self.evolution_count: int = 0
        self._level: int = 1
        self.history: list[dict[str, Any]] = []

    @property
    def level(self) -> int:
        """Current evolution level, derived from evolution_count."""
        level = 1
        for m in self.MILESTONES:
            if self.evolution_count >= m:
                level += 1
        return level

    def evolve(self, description: str = "") -> dict[str, Any]:
        """Record one evolution cycle."""
        self.evolution_count += 1
        new_level = self.level
        record = {
            "evolution": self.evolution_count,
            "level": new_level,
            "description": description or f"Evolution #{self.evolution_count}",
        }
        self.history.append(record)
        return record

    def get_stats(self) -> dict[str, Any]:
        """Return evolution statistics."""
        return {
            "evolution_count": self.evolution_count,
            "level": self.level,
            "total_milestones_passed": self.level - 1,
            "history_length": len(self.history),
        }

    def get_status(self) -> dict[str, Any]:
        """Alias for get_stats."""
        return self.get_stats()
