"""Strategic brain — goal planning, long-horizon reasoning."""

import torch
import torch.nn as nn


class StrategicBrain(nn.Module):
    """Long-term planning, resource allocation, multi-step reasoning."""

    def __init__(self, config, elo_system):
        super().__init__()
        self.name = "strategic"
        self.elo = elo_system
        self.specializations = ["planning", "resource_allocation", "long_horizon"]
        self.plan_head = nn.Sequential(
            nn.Linear(config.d_model, config.d_model),
            nn.GELU(),
            nn.Linear(config.d_model, config.d_model),
        )
        self.priority_head = nn.Linear(config.d_model, 1)
        self.confidence_head = nn.Linear(config.d_model, 1)

    def forward(self, x: torch.Tensor) -> dict:
        h = self.plan_head(x)
        priority = torch.sigmoid(self.priority_head(h.mean(1)))
        confidence = torch.sigmoid(self.confidence_head(h.mean(1)))
        return {
            "output": h,
            "confidence": confidence,
            "priority": priority,
            "brain": self.name,
        }
