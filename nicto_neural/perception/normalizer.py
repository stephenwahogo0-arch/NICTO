import numpy as np
import json
from typing import Dict, List, Optional


class FeatureNormalizer:
    def __init__(self, dim: int = 15):
        self.dim = dim
        self.count = 0
        self.mean = np.zeros(dim, dtype=np.float64)
        self.M2 = np.zeros(dim, dtype=np.float64)
        self.std = np.zeros(dim, dtype=np.float64)

    def fit(self, features: np.ndarray) -> None:
        if features.ndim == 1:
            features = features.reshape(1, -1)
        if features.shape[1] != self.dim:
            raise ValueError(f"Expected dim {self.dim}, got {features.shape[1]}")
        self.count = features.shape[0]
        self.mean = np.mean(features, axis=0).astype(np.float64)
        self.M2 = np.sum((features - self.mean) ** 2, axis=0).astype(np.float64)
        variance = self.M2 / self.count
        self.std = np.sqrt(np.maximum(variance, 1e-12))

    def partial_fit(self, feature: np.ndarray) -> None:
        feature = feature.flatten().astype(np.float64)
        if len(feature) != self.dim:
            raise ValueError(f"Expected dim {self.dim}, got {len(feature)}")
        self.count += 1
        delta = feature - self.mean
        self.mean += delta / self.count
        delta2 = feature - self.mean
        self.M2 += delta * delta2
        if self.count > 1:
            variance = self.M2 / (self.count - 1)
            self.std = np.sqrt(np.maximum(variance, 1e-12))

    def normalize(self, features: np.ndarray) -> np.ndarray:
        if features.ndim == 1:
            features = features.reshape(1, -1)
        if self.count == 0:
            return features.copy().astype(np.float32)
        safe_std = np.where(self.std < 1e-12, 1.0, self.std)
        return ((features - self.mean) / safe_std).astype(np.float32)

    def denormalize(self, features: np.ndarray) -> np.ndarray:
        if features.ndim == 1:
            features = features.reshape(1, -1)
        if self.count == 0:
            return features.copy().astype(np.float32)
        return (features * self.std + self.mean).astype(np.float32)

    def state_dict(self) -> Dict:
        return {
            "dim": self.dim,
            "count": self.count,
            "mean": self.mean.tolist(),
            "M2": self.M2.tolist(),
            "std": self.std.tolist(),
        }

    def load_state_dict(self, state: Dict) -> None:
        self.dim = state["dim"]
        self.count = state["count"]
        self.mean = np.array(state["mean"], dtype=np.float64)
        self.M2 = np.array(state["M2"], dtype=np.float64)
        self.std = np.array(state["std"], dtype=np.float64)

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump(self.state_dict(), f)

    def load(self, path: str) -> None:
        with open(path, "r") as f:
            self.load_state_dict(json.load(f))
