"""ELO API — EloSystem query/update interface."""


class EloAPI:
    """Public API for ELO system queries and updates."""

    def __init__(self, elo_system):
        self.elo = elo_system

    def get_rating(self, brain: str, domain: str = "general") -> float:
        return self.elo.get_rating(brain, domain)

    def get_all_ratings(self, brain: str) -> dict:
        return self.elo.get_all_ratings(brain)

    def get_leaderboard(self, domain: str = "general") -> list:
        return self.elo.get_leaderboard(domain)

    def get_best_brain(self, domain: str) -> str:
        return self.elo.select_best_brain(domain)

    def get_history(self, brain: str, domain: str, limit: int = 50) -> list:
        return self.elo.get_history(brain, domain, limit)
