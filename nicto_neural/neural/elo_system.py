import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict


DOMAINS = ["general", "code", "math", "creative", "strategic", "knowledge", "intuitive"]
BRAIN_NAMES = ["primary", "analytical", "creative", "strategic", "knowledge", "intuitive"]


@dataclass
class ELOEntry:
    brain: str
    domain: str
    rating: float = 1500.0
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    k_factor: float = 32.0
    last_updated: float = 0.0


@dataclass
class ELOUpdate:
    brain: str
    domain: str
    old_rating: float
    new_rating: float
    expected: float
    actual: float
    opponent_rating: float


class ELOHistory:
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.updates: List[ELOUpdate] = []

    def add(self, update: ELOUpdate):
        self.updates.append(update)
        if len(self.updates) > self.max_history:
            self.updates = self.updates[-self.max_history:]

    def recent(self, n: int = 10) -> List[ELOUpdate]:
        return self.updates[-n:]

    def trend(self, brain: str, domain: str, n: int = 20) -> float:
        relevant = [u for u in self.updates[-n:] if u.brain == brain and u.domain == domain]
        if len(relevant) < 2:
            return 0.0
        deltas = [u.new_rating - u.old_rating for u in relevant]
        return sum(deltas) / len(deltas)


class ELOEstimator:
    def __init__(self, state_path: Optional[str] = None):
        self.entries: Dict[str, ELOEntry] = {}
        self.history = ELOHistory()
        self.state_path = state_path
        if state_path and os.path.exists(state_path):
            self.load()

    def _key(self, brain: str, domain: str) -> str:
        return f"{brain}:{domain}"

    def get_or_create(self, brain: str, domain: str) -> ELOEntry:
        key = self._key(brain, domain)
        if key not in self.entries:
            self.entries[key] = ELOEntry(brain=brain, domain=domain)
        return self.entries[key]

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))

    def update(
        self,
        brain: str,
        domain: str,
        won: bool,
        opponent_rating: float = 1500.0,
        k_factor: Optional[float] = None,
    ) -> ELOUpdate:
        entry = self.get_or_create(brain, domain)
        k = k_factor if k_factor is not None else entry.k_factor
        expected = self.expected_score(entry.rating, opponent_rating)
        actual = 1.0 if won else 0.0
        old_rating = entry.rating
        entry.rating += k * (actual - expected)
        entry.games_played += 1
        if won:
            entry.wins += 1
        else:
            entry.losses += 1

        update = ELOUpdate(
            brain=brain,
            domain=domain,
            old_rating=old_rating,
            new_rating=entry.rating,
            expected=expected,
            actual=actual,
            opponent_rating=opponent_rating,
        )
        self.history.add(update)
        return update

    def get_rating(self, brain: str, domain: str) -> float:
        return self.get_or_create(brain, domain).rating

    def best_brain(self, domain: str) -> Tuple[str, float]:
        best = None
        best_rating = -1.0
        for key, entry in self.entries.items():
            if entry.domain == domain:
                if entry.rating > best_rating:
                    best_rating = entry.rating
                    best = entry.brain
        return best or "primary", best_rating if best_rating > 0 else 1500.0

    def brain_rankings(self, domain: str) -> List[Tuple[str, float]]:
        rankings = []
        for brain in BRAIN_NAMES:
            rating = self.get_rating(brain, domain)
            rankings.append((brain, rating))
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings

    def update_k_factor(self, brain: str, domain: str, new_k: float):
        entry = self.get_or_create(brain, domain)
        entry.k_factor = max(4.0, min(200.0, new_k))

    def save(self, path: Optional[str] = None):
        p = path or self.state_path
        if p is None:
            return
        os.makedirs(os.path.dirname(p), exist_ok=True)
        data = {
            "entries": {k: asdict(v) for k, v in self.entries.items()},
        }
        with open(p, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path: Optional[str] = None):
        p = path or self.state_path
        if p is None or not os.path.exists(p):
            return
        with open(p) as f:
            data = json.load(f)
        for k, v in data["entries"].items():
            self.entries[k] = ELOEntry(**v)
