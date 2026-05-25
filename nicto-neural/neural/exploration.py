"""Exploration manager — ε-greedy + Gaussian noise injection."""

import random

import torch


class ExplorationManager:
    """ε-greedy exploration + Gaussian noise injection. Both strategies active simultaneously."""

    def __init__(self, config):
        self.epsilon = config.epsilon_start
        self.epsilon_start = config.epsilon_start
        self.epsilon_end = config.epsilon_end
        self.epsilon_decay = config.epsilon_decay
        self.noise_std = config.noise_std
        self.steps = 0

    def should_explore(self) -> bool:
        """ε-greedy: explore with probability ε."""
        self.steps += 1
        decay_progress = max(0.0, (self.epsilon_decay - self.steps) / self.epsilon_decay)
        self.epsilon = max(self.epsilon_end, self.epsilon_start * decay_progress)
        return random.random() < self.epsilon

    def add_noise(self, weights) -> None:
        """Add Gaussian noise to model weights for exploration."""
        with torch.no_grad():
            for param in weights:
                param.add_(torch.randn_like(param) * self.noise_std)

    def get_epsilon(self) -> float:
        return self.epsilon

    def get_stats(self) -> dict:
        return {
            "epsilon": self.epsilon,
            "steps": self.steps,
            "noise_std": self.noise_std,
        }
