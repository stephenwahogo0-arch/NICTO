import numpy as np
import pandas as pd
from nikto.predict.models import EloModel, LogisticModel, XGBoostModel, EnsembleModel, ArimaModel
from nikto.predict.features import FeatureEngineer
from nikto.predict.backtest import BacktestEngine
from nikto.predict.data import DataFeed, MockDataFeed


class PredictionEngine:
    def __init__(self):
        self.elo = EloModel()
        self.logistic = LogisticModel()
        self.xgboost = XGBoostModel()
        self.ensemble = EnsembleModel()
        self.arima = ArimaModel()
        self.features = FeatureEngineer()
        self.backtest = BacktestEngine()
        self.data = MockDataFeed()
        self._trained = False

    def ingest_matches(self, matches):
        self.data.seed_historical("generic", "league", matches)
        self.features.ingest_bulk(matches)
        for m in matches:
            winner = 1 if m["score_a"] > m["score_b"] else (0 if m["score_a"] < m["score_b"] else 0.5)
            self.elo.update(m["team_a"], m["team_b"], winner)

    def ingest_from_feed(self, feed: DataFeed, sport="soccer", league="premier-league"):
        self.data = feed
        matches = feed.fetch_historical(sport, league)
        if matches:
            self.ingest_matches(matches)
        return len(matches)

    def train_models(self):
        teams = list(set(
            list(self.features._team_history.keys())
        ))
        if len(teams) < 2:
            return {"status": "insufficient_data", "teams": len(teams)}

        X, y = [], []
        for team_a in teams:
            for team_b in teams:
                if team_a == team_b:
                    continue
                history = self.features._team_history[team_a]
                for match in history:
                    if match["opponent"] == team_b:
                        fv = self.features.feature_vector(team_a, team_b)
                        if not np.any(np.isnan(fv)):
                            X.append(fv)
                            y.append(1 if match["scored"] > match["conceded"] else 0)

        if len(X) < 10:
            return {"status": "insufficient_samples", "samples": len(X)}

        X = np.array(X)
        y = np.array(y)
        fnames = self.features.feature_names()

        self.logistic.fit(X, y, fnames)
        self.xgboost.fit(X, y, fnames)
        self.ensemble.add_model("elo", self.elo, weight=1.0)
        self.ensemble.add_model("logistic", self.logistic, weight=2.0)
        self.ensemble.add_model("xgboost", self.xgboost, weight=3.0)
        self._trained = True

        bt = self.backtest.run(self.ensemble, X, y, "ensemble")
        return {"status": "trained", "samples": len(X), "teams": len(teams), "accuracy": bt.get("accuracy")}

    def predict_matchup(self, team_a, team_b):
        if not self._trained:
            fv = self.features.feature_vector(team_a, team_b)
            return self.elo.predict_matchup(team_a, team_b)

        fv = self.features.feature_vector(team_a, team_b)
        elo_pred = self.elo.predict_matchup(team_a, team_b)
        logistic_pred = self.logistic.predict_matchup(fv)
        xgb_pred = self.xgboost.predict_matchup(fv)
        ensemble_pred = self.ensemble.predict_matchup(fv, team_a=team_a, team_b=team_b)

        return {
            "matchup": {"team_a": team_a, "team_b": team_b},
            "predictions": {
                "elo": {"probability": elo_pred["prob_a"], "confidence": abs(elo_pred["prob_a"] - 0.5) * 2},
                "logistic": {"probability": logistic_pred["probability"], "confidence": logistic_pred["confidence"]},
                "xgboost": {"probability": xgb_pred["probability"], "confidence": xgb_pred["confidence"]},
                "ensemble": ensemble_pred,
            },
            "features": {k: float(v) for k, v in fv.items()} if isinstance(fv, dict) else fv.tolist(),
        }

    def predict_market(self, ohlcv_data, horizon_days=30):
        df = pd.DataFrame(ohlcv_data) if isinstance(ohlcv_data, list) and len(ohlcv_data) > 0 and isinstance(ohlcv_data[0], dict) else ohlcv_data
        if isinstance(df, pd.DataFrame) and "close" in df.columns:
            series = df["close"].values
            forecast = self.arima.predict_trend(series, steps=horizon_days)
            features = self.features.ohlcv_features(df)
            return {**forecast, "indicators": features}
        return {"error": "invalid OHLCV data"}

    def backtest_strategy(self, model_name="ensemble", window=100):
        teams = list(self.features._team_history.keys())
        if len(teams) < 2:
            return {"error": "insufficient data"}

        X, y = [], []
        for team_a in teams:
            for team_b in teams:
                if team_a == team_b:
                    continue
                for match in self.features._team_history[team_a]:
                    if match["opponent"] == team_b:
                        fv = self.features.feature_vector(team_a, team_b)
                        if not np.any(np.isnan(fv)):
                            X.append(fv)
                            y.append(1 if match["scored"] > match["conceded"] else 0)

        if len(X) < window + 10:
            return {"error": f"need at least {window + 10} samples, have {len(X)}"}

        X = np.array(X)
        y = np.array(y)

        def make_model():
            return LogisticModel()

        bt = self.backtest.run_sequential(make_model, X, y, window=window)
        return bt

    def compare_all_models(self):
        return self.backtest.compare_models()

    def summary(self):
        lines = ["Predictive Intelligence Engine"]
        lines.append("=" * 60)
        lines.append(f"  Teams tracked: {len(self.features._team_history)}")
        lines.append(f"  Models trained: {self._trained}")
        lines.append(f"  Sample data available: {self.data._historical.get('generic:league', [])[:1] != []}")
        if self._trained:
            lines.append(self.backtest.summary())
        return "\n".join(lines)
