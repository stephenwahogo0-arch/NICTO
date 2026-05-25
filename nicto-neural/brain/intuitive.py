"""Intuitive brain — fast pattern matching, manages exploration rate."""

import torch
import torch.nn as nn


class IntuitiveBrain(nn.Module):
    """Fast pattern matching. Confidence estimation. ε-greedy brain selection master."""

    def __init__(self, config, elo_system, exploration_manager):
        super().__init__()
        self.name = "intuitive"
        self.elo = elo_system
        self.explorer = exploration_manager
        self.pattern_head = nn.Linear(config.d_model, 64)
        self.confidence_head = nn.Linear(64, 1)
        self.specializations = ["ranking", "confidence", "exploration"]

    def get_exploration_rate(self) -> float:
        return self.explorer.get_epsilon()

    def should_explore(self) -> bool:
        return self.explorer.should_explore()

    def forward(self, x: torch.Tensor) -> dict:
        patterns = torch.relu(self.pattern_head(x.mean(1)))
        confidence = torch.sigmoid(self.confidence_head(patterns))
        return {
            "confidence": confidence,
            "explore": self.should_explore(),
            "epsilon": self.get_exploration_rate(),
            "brain": self.name,
        }
