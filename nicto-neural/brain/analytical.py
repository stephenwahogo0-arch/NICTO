"""Analytical brain — logic, code, mathematics, formal reasoning."""

import torch
import torch.nn as nn


class AnalyticalBrain(nn.Module):
    """Logic, code, mathematics — highest ELO for technical domains."""

    def __init__(self, config, elo_system):
        super().__init__()
        self.name = "analytical"
        self.elo = elo_system
        self.specializations = ["code", "math", "logic"]
        self.reasoning_head = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2),
            nn.GELU(),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.confidence_head = nn.Linear(config.d_model, 1)
        self.step_counter = 0

    def forward(self, x: torch.Tensor) -> dict:
        h = self.reasoning_head(x)
        confidence = torch.sigmoid(self.confidence_head(h.mean(1)))
        self.step_counter += 1
        return {
            "output": h,
            "confidence": confidence,
            "brain": self.name,
            "steps": self.step_counter,
        }
