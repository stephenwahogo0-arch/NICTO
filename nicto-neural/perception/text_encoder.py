"""Text encoder — TransformerCore wrapper for encoding text."""

import torch
import torch.nn as nn


class TextEncoder(nn.Module):
    """Encodes text input into feature vectors using transformer backbone."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.projection = nn.Linear(config.d_model, config.d_model)
        self.norm = nn.LayerNorm(config.d_model)

    def forward(self, transformer_output: torch.Tensor) -> torch.Tensor:
        projected = self.projection(transformer_output)
        return self.norm(projected)

    def encode_pooled(self, transformer_output: torch.Tensor) -> torch.Tensor:
        """Mean-pool across sequence length to get fixed-size representation."""
        encoded = self.forward(transformer_output)
        return encoded.mean(dim=1)
