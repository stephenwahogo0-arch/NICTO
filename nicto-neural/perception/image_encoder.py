"""Image encoder — simple CNN encoder for visual features."""

import torch
import torch.nn as nn


class ImageEncoder(nn.Module):
    """Simple CNN encoder for image features, projects to d_model."""

    def __init__(self, config, in_channels: int = 3):
        super().__init__()
        self.config = config
        self.features = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4)),
        )
        self.projection = nn.Linear(128 * 4 * 4, config.d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.features(x)
        features = features.view(features.size(0), -1)
        return self.projection(features)
