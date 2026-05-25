"""Audio encoder — 1D conv encoder for audio features."""

import torch
import torch.nn as nn


class AudioEncoder(nn.Module):
    """1D convolutional encoder for audio features, projects to d_model."""

    def __init__(self, config, in_channels: int = 1):
        super().__init__()
        self.config = config
        self.features = nn.Sequential(
            nn.Conv1d(in_channels, 32, kernel_size=7, stride=2, padding=3),
            nn.ReLU(),
            nn.Conv1d(32, 64, kernel_size=5, stride=2, padding=2),
            nn.ReLU(),
            nn.Conv1d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(16),
        )
        self.projection = nn.Linear(128 * 16, config.d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.features(x)
        features = features.view(features.size(0), -1)
        return self.projection(features)
