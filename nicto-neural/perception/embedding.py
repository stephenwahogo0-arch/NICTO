"""Embedding layer with weight tying support."""

import math

import torch
import torch.nn as nn


class NictoEmbedding(nn.Module):
    """nn.Embedding wrapper with weight tying and scaling."""

    def __init__(self, vocab_size: int, d_model: int):
        super().__init__()
        self.d_model = d_model
        self.embedding = nn.Embedding(vocab_size, d_model)
        self._init_weights()

    def _init_weights(self) -> None:
        nn.init.normal_(self.embedding.weight, mean=0.0, std=self.d_model ** -0.5)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.embedding(x) * math.sqrt(self.d_model)

    def tie_weights(self, output_projection: nn.Linear) -> None:
        """Tie embedding weights with output projection."""
        output_projection.weight = self.embedding.weight
