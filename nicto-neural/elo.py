from typing import Dict, Optional
from collections import defaultdict


class ELOEstimator:
    def __init__(self, k_factor: int = 32, default_rating: int = 1200):
        self.k_factor = k_factor
        self.default_rating = default_rating
        self.ratings: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(lambda: default_rating))

    def get_rating(self, brain: str, domain: str) -> int:
        return self.ratings[brain].get(domain, self.default_rating)

    def update(self, brain: str, domain: str, won: bool, opponent_rating: int) -> int:
        rating = self.get_rating(brain, domain)
        expected = 1.0 / (1.0 + 10.0 ** ((opponent_rating - rating) / 400.0))
        score = 1.0 if won else 0.0
        new_rating = rating + self.k_factor * (score - expected)
        new_rating = max(100, int(round(new_rating)))
        self.ratings[brain][domain] = new_rating
        return new_rating

    def best_brain(self, domain: str) -> Optional[str]:
        best = None
        best_rating = -1
        for brain, domains in self.ratings.items():
            r = domains.get(domain, self.default_rating)
            if r > best_rating:
                best_rating = r
                best = brain
        return best

    def set_rating(self, brain: str, domain: str, rating: int) -> None:
        self.ratings[brain][domain] = max(100, rating)

    def all_ratings(self) -> Dict[str, Dict[str, int]]:
        return {k: dict(v) for k, v in self.ratings.items()}
