import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import log_loss, brier_score_loss, accuracy_score
from sklearn.calibration import CalibratedClassifierCV
from statsmodels.tsa.arima.model import ARIMA as ARIMA_Model
import warnings


class EloModel:
    def __init__(self, k_factor=32, home_advantage=100, initial_rating=1500):
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.ratings = {}
        self.initial_rating = initial_rating

    def get_rating(self, team):
        return self.ratings.get(team, self.initial_rating)

    def expected_score(self, rating_a, rating_b):
        return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))

    def predict(self, team_a, team_b, neutral=False):
        ra = self.get_rating(team_a) + (0 if neutral else self.home_advantage)
        rb = self.get_rating(team_b)
        return self.expected_score(ra, rb)

    def update(self, team_a, team_b, result, neutral=False):
        ra = self.get_rating(team_a) + (0 if neutral else self.home_advantage)
        rb = self.get_rating(team_b)
        ea = self.expected_score(ra, rb)
        eb = 1.0 - ea
        self.ratings[team_a] = self.get_rating(team_a) + self.k_factor * (result - ea)
        self.ratings[team_b] = self.get_rating(team_b) + self.k_factor * ((1 - result) - eb)

    def predict_matchup(self, team_a, team_b, neutral=False):
        prob_a = self.predict(team_a, team_b, neutral)
        return {"team_a": team_a, "team_b": team_b, "prob_a": prob_a, "prob_b": 1.0 - prob_a,
                "probability": prob_a, "model": "elo"}


class LogisticModel:
    def __init__(self):
        self.model = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, class_weight="balanced")
        self._fitted = False
        self._feature_names = []

    @property
    def fitted(self):
        return self._fitted

    def fit(self, X, y, feature_names=None):
        self.model.fit(X, y)
        self._fitted = True
        self._feature_names = feature_names or [f"f{i}" for i in range(X.shape[1])]
        return self

    def predict(self, X):
        return self.model.predict_proba(X)[:, 1]

    def predict_matchup(self, features):
        X = np.array(features).reshape(1, -1)
        prob = self.model.predict_proba(X)[0, 1]
        return {"probability": float(prob), "confidence": float(abs(prob - 0.5) * 2), "model": "logistic"}

    def feature_importance(self):
        return dict(zip(self._feature_names, self.model.coef_[0].tolist()))


class XGBoostModel:
    def __init__(self, n_estimators=200, max_depth=6, learning_rate=0.1):
        self.model = GradientBoostingClassifier(
            n_estimators=n_estimators, max_depth=max_depth,
            learning_rate=learning_rate, subsample=0.8, random_state=42
        )
        self._fitted = False
        self._feature_names = []

    @property
    def fitted(self):
        return self._fitted

    def fit(self, X, y, feature_names=None):
        self.model.fit(X, y)
        self._fitted = True
        self._feature_names = feature_names or [f"f{i}" for i in range(X.shape[1])]
        return self

    def predict(self, X):
        return self.model.predict_proba(X)[:, 1]

    def predict_matchup(self, features):
        X = np.array(features).reshape(1, -1)
        prob = self.model.predict_proba(X)[0, 1]
        return {"probability": float(prob), "confidence": float(abs(prob - 0.5) * 2), "model": "xgboost"}

    def feature_importance(self):
        imp = self.model.feature_importances_
        return dict(zip(self._feature_names, imp.tolist()))


class EnsembleModel:
    def __init__(self):
        self.models = {}
        self.weights = {}

    def add_model(self, name, model, weight=1.0):
        self.models[name] = model
        self.weights[name] = weight

    def predict_matchup(self, features=None, team_a=None, team_b=None):
        predictions = []
        total_weight = 0.0
        for name, model in self.models.items():
            w = self.weights.get(name, 1.0)
            try:
                if name == "elo":
                    if team_a and team_b:
                        result = model.predict_matchup(team_a, team_b)
                    else:
                        continue
                elif hasattr(model, "predict_matchup"):
                    result = model.predict_matchup(features)
                elif hasattr(model, "predict"):
                    X = np.array(features).reshape(1, -1) if isinstance(features, np.ndarray) else np.array(features).reshape(1, -1)
                    prob = model.predict(X)[0]
                    result = {"probability": prob, "model": name}
                else:
                    continue
            except Exception:
                continue
            predictions.append((result["probability"], w))
            total_weight += w

        if not predictions:
            return {"probability": 0.5, "confidence": 0.0, "model": "ensemble", "components": []}

        weighted_prob = sum(p * w for p, w in predictions) / total_weight
        confidence = float(abs(weighted_prob - 0.5) * 2)

        return {
            "probability": float(weighted_prob),
            "confidence": confidence,
            "model": "ensemble",
            "components": [{"model": name, "prob": p} for name, (p, w) in zip(self.models.keys(), [(p, w) for p, w in predictions])],
        }


class ArimaModel:
    def __init__(self, order=(5, 1, 0)):
        self.order = order
        self._fitted = None

    def fit(self, series):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._fitted = ARIMA_Model(series, order=self.order).fit()
        return self

    def forecast(self, steps=10):
        if self._fitted is None:
            return None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return self._fitted.forecast(steps=steps).tolist()

    def predict_trend(self, series, steps=10):
        self.fit(series)
        forecast = self.forecast(steps)
        direction = "up" if forecast and forecast[-1] > series[-1] else "down"
        return {"forecast": forecast, "direction": direction, "steps": steps, "model": "arima"}
