from typing import Dict, List, Optional, Tuple


class ELOAPI:
    def __init__(self, elo_system=None):
        self._elo = elo_system

    def get_rating(self, brain: str, domain: str) -> float:
        if self._elo is None:
            return 1500.0
        return self._elo.get_rating(brain, domain)

    def update_elo(self, brain: str, domain: str, won: bool, opponent_rating: float = 1500.0) -> Dict:
        if self._elo is None:
            return {"error": "ELOEstimator not initialized"}
        update = self._elo.update(brain, domain, won, opponent_rating)
        return {
            "brain": update.brain,
            "domain": update.domain,
            "old_rating": update.old_rating,
            "new_rating": update.new_rating,
            "expected": update.expected,
            "actual": update.actual,
        }

    def rankings(self, domain: str) -> List[Tuple[str, float]]:
        if self._elo is None:
            return []
        return self._elo.brain_rankings(domain)

    def set_elo_system(self, elo_system):
        self._elo = elo_system
