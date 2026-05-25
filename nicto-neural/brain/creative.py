"""Creative brain — generation, design, brainstorming with higher temperature."""

import torch
import torch.nn as nn


class CreativeBrain(nn.Module):
    """Novel ideas, artistic generation, lateral thinking."""

    def __init__(self, config, elo_system):
        super().__init__()
        self.name = "creative"
        self.elo = elo_system
        self.specializations = ["generation", "design", "brainstorming"]
        self.creative_head = nn.Sequential(
            nn.Linear(config.d_model, config.d_model * 2),
            nn.GELU(),
            nn.Dropout(config.dropout * 1.5),
            nn.Linear(config.d_model * 2, config.d_model),
        )
        self.confidence_head = nn.Linear(config.d_model, 1)
        self.temperature = 0.8

    def forward(self, x: torch.Tensor) -> dict:
        h = self.creative_head(x)
        confidence = torch.sigmoid(self.confidence_head(h.mean(1)))
        return {
            "output": h,
            "confidence": confidence,
            "brain": self.name,
            "temperature": self.temperature,
        }
