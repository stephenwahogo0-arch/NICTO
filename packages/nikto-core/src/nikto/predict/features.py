import numpy as np
import pandas as pd
from collections import defaultdict


class FeatureEngineer:
    def __init__(self):
        self._team_history = defaultdict(list)

    def ingest_match(self, team_a, team_b, score_a, score_b, date=None):
        self._team_history[team_a].append({"opponent": team_b, "scored": score_a, "conceded": score_b, "date": date or 0})
        self._team_history[team_b].append({"opponent": team_a, "scored": score_b, "conceded": score_a, "date": date or 0})

    def ingest_bulk(self, matches):
        for m in matches:
            self.ingest_match(m["team_a"], m["team_b"], m["score_a"], m["score_b"], m.get("date"))

    def features_for_matchup(self, team_a, team_b, window=10):
        ha = self._team_history.get(team_a, [])
        hb = self._team_history.get(team_b, [])
        ha_recent = ha[-window:] if len(ha) >= window else ha
        hb_recent = hb[-window:] if len(hb) >= window else hb

        def form_features(history, team):
            if not history:
                return [0.5, 0, 0, 0, 0, 0, 0]
            scored = np.array([m["scored"] for m in history])
            conceded = np.array([m["conceded"] for m in history])
            wins = np.sum(scored > conceded) / max(len(history), 1)
            avg_scored = float(np.mean(scored))
            avg_conceded = float(np.mean(conceded))
            streak = 0
            for m in reversed(history):
                if m["scored"] > m["conceded"]:
                    streak = 1
                    break
                elif m["scored"] < m["conceded"]:
                    streak = -1
                    break
            total_goals = float(np.mean(scored + conceded))
            recent_form = sum(1 for m in history[-5:] if m["scored"] > m["conceded"]) / max(min(5, len(history)), 1)
            return [wins, avg_scored, avg_conceded, streak, total_goals, recent_form, len(history)]

        fa = form_features(ha_recent, team_a)
        fb = form_features(hb_recent, team_b)

        h2h = [m for m in ha if m["opponent"] == team_b]
        h2h_wins = sum(1 for m in h2h if m["scored"] > m["conceded"]) / max(len(h2h), 1)

        return {
            "team_a_win_rate": fa[0], "team_a_avg_scored": fa[1], "team_a_avg_conceded": fa[2],
            "team_a_streak": fa[3], "team_a_total_goals": fa[4], "team_a_recent_form": fa[5],
            "team_a_matches": fa[6],
            "team_b_win_rate": fb[0], "team_b_avg_scored": fb[1], "team_b_avg_conceded": fb[2],
            "team_b_streak": fb[3], "team_b_total_goals": fb[4], "team_b_recent_form": fb[5],
            "team_b_matches": fb[6],
            "h2h_win_rate_a": h2h_wins, "h2h_matches": len(h2h),
        }

    def feature_vector(self, team_a, team_b, window=10):
        f = self.features_for_matchup(team_a, team_b, window)
        return np.array([
            f["team_a_win_rate"], f["team_a_avg_scored"], f["team_a_avg_conceded"],
            f["team_a_streak"], f["team_a_recent_form"], f["team_a_matches"],
            f["team_b_win_rate"], f["team_b_avg_scored"], f["team_b_avg_conceded"],
            f["team_b_streak"], f["team_b_recent_form"], f["team_b_matches"],
            f["h2h_win_rate_a"], f["h2h_matches"],
        ], dtype=np.float64)

    def feature_names(self):
        return [
            "team_a_win_rate", "team_a_avg_scored", "team_a_avg_conceded",
            "team_a_streak", "team_a_recent_form", "team_a_matches",
            "team_b_win_rate", "team_b_avg_scored", "team_b_avg_conceded",
            "team_b_streak", "team_b_recent_form", "team_b_matches",
            "h2h_win_rate_a", "h2h_matches",
        ]

    def ohlcv_features(self, df, window=5):
        if len(df) < window + 1:
            return {}
        closes = df["close"].values
        volumes = df["volume"].values if "volume" in df.columns else np.ones(len(df))
        returns = np.diff(closes) / closes[:-1]
        sma = np.mean(closes[-window:])
        ema = self._ema(closes, window)
        upper = sma + 2 * np.std(closes[-window:])
        lower = sma - 2 * np.std(closes[-window:])
        atr = self._atr(df, window)
        return {
            "last_price": float(closes[-1]),
            "sma": float(sma), "ema": float(ema),
            "upper_band": float(upper), "lower_band": float(lower),
            "atr": float(atr),
            "volatility": float(np.std(returns[-window:])),
            "momentum": float(returns[-1]) if len(returns) > 0 else 0.0,
            "volume_ratio": float(volumes[-1] / np.mean(volumes[-window:])) if window > 0 else 1.0,
        }

    def _ema(self, data, period):
        multiplier = 2.0 / (period + 1)
        result = data[0]
        for price in data[1:]:
            result = (price - result) * multiplier + result
        return result

    def _atr(self, df, period):
        if "high" not in df.columns or "low" not in df.columns:
            return 0.0
        high_low = df["high"].values - df["low"].values
        return float(np.mean(high_low[-period:])) if len(high_low) >= period else float(np.mean(high_low))
