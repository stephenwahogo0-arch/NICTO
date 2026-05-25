from typing import Any, Dict, List, Optional


class EvolutionAPI:
    def __init__(self, evolution_engine=None):
        self._engine = evolution_engine

    def evaluate(self, task_history: List[Dict] = None) -> Dict:
        if self._engine is None:
            return {"error": "EvolutionEngine not initialized"}
        return self._engine.score_current()

    def trigger_training(self, reason: str = "manual") -> Dict:
        if self._engine is None:
            return {"error": "EvolutionEngine not initialized"}
        task_id = self._engine.trigger_training(reason)
        return {"training_triggered": True, "task_id": task_id}

    def get_milestones(self) -> List[Dict]:
        if self._engine is None:
            return []
        return [{"generation": 0, "score": 0.5}]

    def set_engine(self, engine):
        self._engine = engine