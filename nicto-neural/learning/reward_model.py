"""Reward model — learned reward function for RL training."""

import torch
import torch.nn as nn
import torch.nn.functional as F


class RewardModel(nn.Module):
    """Learned reward model that predicts task quality from features."""

    def __init__(self, config, state_dim: int = 15):
        super().__init__()
        self.config = config
        self.network = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )
        self.optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        self._history: list[dict] = []

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(features)

    def predict_reward(self, features: torch.Tensor) -> float:
        """Predict reward for given task features."""
        with torch.no_grad():
            return float(self.forward(features).squeeze())

    def train_step(self, features: torch.Tensor, target_reward: float) -> float:
        """Single training step on (features, reward) pair."""
        self.optimizer.zero_grad()
        predicted = self.forward(features).squeeze()
        target = torch.tensor(target_reward, dtype=torch.float32)
        loss = F.mse_loss(predicted, target)
        loss.backward()
        self.optimizer.step()
        self._history.append({"loss": loss.item()})
        return loss.item()

    def get_training_stats(self) -> dict:
        if not self._history:
            return {"steps": 0, "avg_loss": 0.0}
        recent = self._history[-100:]
        return {
            "steps": len(self._history),
            "avg_loss": sum(h["loss"] for h in recent) / len(recent),
        }
