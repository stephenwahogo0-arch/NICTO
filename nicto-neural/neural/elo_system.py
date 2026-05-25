"""ELO rating system — per-brain, per-domain performance tracking."""

import datetime
import json
import sqlite3
from pathlib import Path

from .tensor_ops import elo_expected, elo_update


class EloRating:
    """Per-brain, per-domain ELO rating."""

    def __init__(self, brain_name: str, domain: str, rating: float = 1500.0):
        self.brain_name = brain_name
        self.domain = domain
        self.rating = float(rating)
        self.games_played = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0

    def to_dict(self) -> dict:
        return {
            "brain": self.brain_name,
            "domain": self.domain,
            "rating": self.rating,
            "games": self.games_played,
        }


class EloSystem:
    """ELO rating manager for all brains. Updates after every task completion."""

    BASE_RATING = 1500
    K_FACTOR = 32

    def __init__(self, config, db_path: str = None):
        self.config = config
        self.db_path = db_path or "~/.nicto/neural/elo.db"
        self._ratings: dict[str, dict[str, EloRating]] = {}
        self._init_ratings()
        self._init_db()

    def _init_ratings(self):
        for brain in self.config.brain_names:
            self._ratings[brain] = {}
            for domain in self.config.elo_domains:
                self._ratings[brain][domain] = EloRating(
                    brain, domain, self.BASE_RATING
                )

    def _init_db(self):
        path = Path(self.db_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path))
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS elo_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brain TEXT,
                domain TEXT,
                old_rating REAL,
                new_rating REAL,
                actual_score REAL,
                timestamp TEXT
            )
        """)
        self._conn.commit()

    def get_rating(self, brain: str, domain: str = "general") -> float:
        if brain not in self._ratings:
            return float(self.BASE_RATING)
        rating_obj = self._ratings[brain].get(domain)
        if rating_obj is None:
            return float(self.BASE_RATING)
        return rating_obj.rating

    def get_all_ratings(self, brain: str) -> dict:
        return {
            domain: r.rating
            for domain, r in self._ratings.get(brain, {}).items()
        }

    def update(
        self,
        brain_name: str,
        domain: str,
        actual_score: float,
        opponent_rating: float = None,
    ) -> float:
        if opponent_rating is None:
            opponent_rating = float(self.BASE_RATING)

        if brain_name not in self._ratings:
            self._ratings[brain_name] = {}
        if domain not in self._ratings[brain_name]:
            self._ratings[brain_name][domain] = EloRating(
                brain_name, domain, self.BASE_RATING
            )

        rating_obj = self._ratings[brain_name][domain]
        old_rating = rating_obj.rating

        expected = elo_expected(old_rating, opponent_rating)
        new_rating = elo_update(old_rating, expected, actual_score, self.K_FACTOR)

        rating_obj.rating = new_rating
        rating_obj.games_played += 1
        if actual_score == 1.0:
            rating_obj.wins += 1
        elif actual_score == 0.0:
            rating_obj.losses += 1
        else:
            rating_obj.draws += 1

        self._conn.execute(
            """INSERT INTO elo_history
            (brain, domain, old_rating, new_rating, actual_score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                brain_name, domain, old_rating, new_rating,
                actual_score, datetime.datetime.utcnow().isoformat(),
            ),
        )
        self._conn.commit()
        return new_rating - old_rating

    def select_best_brain(
        self, domain: str, candidate_brains: list = None
    ) -> str:
        if candidate_brains is None:
            candidate_brains = self.config.brain_names
        return max(
            candidate_brains,
            key=lambda b: self.get_rating(b, domain),
        )

    def get_leaderboard(self, domain: str = "general") -> list:
        ratings = [
            (brain, self.get_rating(brain, domain))
            for brain in self.config.brain_names
        ]
        return sorted(ratings, key=lambda x: x[1], reverse=True)

    def get_history(self, brain: str, domain: str, limit: int = 50) -> list:
        cursor = self._conn.execute(
            """SELECT old_rating, new_rating, actual_score, timestamp
            FROM elo_history WHERE brain=? AND domain=?
            ORDER BY id DESC LIMIT ?""",
            (brain, domain, limit),
        )
        return cursor.fetchall()
