import json
import os
import time
from typing import Optional


class DataFeed:
    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or os.path.expanduser("~/.nikto/odds_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_odds(self, sport, league, event=None):
        raise NotImplementedError("Subclasses must implement fetch_odds")

    def fetch_historical(self, sport, league, days=365):
        raise NotImplementedError("Subclasses must implement fetch_historical")

    def _cache_get(self, key, max_age_sec=300):
        path = os.path.join(self.cache_dir, f"{key}.json")
        if not os.path.exists(path):
            return None
        age = time.time() - os.path.getmtime(path)
        if age > max_age_sec:
            return None
        with open(path) as f:
            return json.load(f)

    def _cache_set(self, key, data):
        path = os.path.join(self.cache_dir, f"{key}.json")
        with open(path, "w") as f:
            json.dump(data, f)


class MockDataFeed(DataFeed):
    def __init__(self):
        super().__init__()
        self._odds = {}
        self._historical = {}

    def seed_odds(self, sport, league, odds_data):
        self._odds[f"{sport}:{league}"] = odds_data

    def seed_historical(self, sport, league, matches):
        self._historical[f"{sport}:{league}"] = matches

    def fetch_odds(self, sport, league, event=None):
        key = f"{sport}:{league}"
        data = self._odds.get(key, [])
        if event:
            return [d for d in data if event.lower() in str(d).lower()]
        return data

    def fetch_historical(self, sport, league, days=365):
        key = f"{sport}:{league}"
        matches = self._historical.get(key, [])
        if days:
            cutoff = time.time() - days * 86400
            return [m for m in matches if m.get("timestamp", cutoff) >= cutoff]
        return matches

    def generate_sample_data(self, num_teams=20, num_matches=500):
        import random
        teams = [f"Team_{i}" for i in range(num_teams)]
        matches = []
        for _ in range(num_matches):
            a, b = random.sample(teams, 2)
            sa, sb = random.randint(0, 5), random.randint(0, 5)
            matches.append({
                "team_a": a, "team_b": b, "score_a": sa, "score_b": sb,
                "timestamp": time.time() - random.randint(0, 365 * 86400),
                "date": f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            })
        self.seed_historical("soccer", "premier-league", matches)

        odds = []
        for i in range(0, num_matches, 2):
            if i + 1 < len(matches):
                m = matches[i]
                odds.append({
                    "team_a": m["team_a"], "team_b": m["team_b"],
                    "odds_a": round(random.uniform(1.2, 5.0), 2),
                    "odds_b": round(random.uniform(1.2, 5.0), 2),
                    "odds_draw": round(random.uniform(2.5, 4.5), 2),
                })
        self.seed_odds("soccer", "premier-league", odds)
        return matches
