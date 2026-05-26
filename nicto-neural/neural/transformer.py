"""Transformer core — shared backbone for all 6 brains."""

import math

import torch
import torch.nn as nn

from .attention import MultiHeadAttention
from .positional import SinusoidalPositionalEncoding


class TransformerBlock(nn.Module):
    """Single transformer block: MHA → Add&Norm → FFN → Add&Norm."""

    def __init__(self, config):
        super().__init__()
        self.attention = MultiHeadAttention(config)
        self.norm1 = nn.LayerNorm(config.d_model)
        self.norm2 = nn.LayerNorm(config.d_model)
        self.ffn = nn.Sequential(
            nn.Linear(config.d_model, config.d_ff),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_ff, config.d_model),
            nn.Dropout(config.dropout),
        )
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor, mask: torch.Tensor = None) -> torch.Tensor:
        attn_out = self.attention(x, x, x, mask)
        x = self.norm1(x + self.dropout(attn_out))
        ffn_out = self.ffn(x)
        x = self.norm2(x + ffn_out)
        return x


class TransformerCore(nn.Module):
    """Full transformer stack — N TransformerBlocks. Shared backbone for all 6 brains."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.positional = SinusoidalPositionalEncoding(
            config.d_model, config.max_seq_len
        )
        self.blocks = nn.ModuleList([
            TransformerBlock(config) for _ in range(config.n_layers)
        ])
        self.norm = nn.LayerNorm(config.d_model)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor, mask: torch.Tensor = None) -> torch.Tensor:
        x = self.embedding(x) * math.sqrt(self.config.d_model)
        x = self.positional(x)
        x = self.dropout(x)
        for block in self.blocks:
            x = block(x, mask)
        return self.norm(x)

    def get_embeddings(self, x: torch.Tensor) -> torch.Tensor:
        """Get embeddings without positional encoding."""
        return self.embedding(x) * math.sqrt(self.config.d_model)
