from typing import Any, Dict, List, Optional
from ..reasoning.reflection import ReflectionEngine


class ReflectionAPI:
    def __init__(self, reflection_engine: ReflectionEngine = None):
        self._engine = reflection_engine

    def reflect(self, task: Dict, result: Dict) -> Dict:
        if self._engine is None:
            return {"error": "ReflectionEngine not initialized"}
        return self._engine.reflect(task, result)

    def get_improvements(self, limit: int = 10) -> List[str]:
        if self._engine is None:
            return []
        return [f"Suggestion {i}" for i in range(min(limit, 3))]

    def set_engine(self, engine: ReflectionEngine):
        self._engine = engine