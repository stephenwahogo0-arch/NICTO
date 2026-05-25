"""Feature normalizer — online normalization for 15-dim feature vectors."""

import torch


class FeatureNormalizer:
    """Online normalization preventing high-magnitude features from dominating."""

    def __init__(self, n_features: int = 15):
        self.n_features = n_features
        self.mean = torch.zeros(n_features)
        self.std = torch.ones(n_features)
        self.n_samples = 0
        self._fitted = False

    def fit(self, feature_history: list) -> None:
        if not feature_history:
            return
        stacked = torch.stack(feature_history)
        self.mean = stacked.mean(0)
        self.std = stacked.std(0) + 1e-8
        self.n_samples = len(feature_history)
        self._fitted = True

    def transform(self, features: torch.Tensor) -> torch.Tensor:
        if not self._fitted:
            return features
        return (features - self.mean) / self.std

    def fit_transform(self, feature_history: list) -> list:
        self.fit(feature_history)
        return [self.transform(f) for f in feature_history]

    def inverse_transform(self, features: torch.Tensor) -> torch.Tensor:
        return features * self.std + self.mean

    def save(self, path: str) -> None:
        torch.save({
            "mean": self.mean,
            "std": self.std,
            "n_samples": self.n_samples,
            "fitted": self._fitted,
        }, path)

    def load(self, path: str) -> None:
        state = torch.load(path, weights_only=True)
        self.mean = state["mean"]
        self.std = state["std"]
        self.n_samples = state["n_samples"]
        self._fitted = state["fitted"]
