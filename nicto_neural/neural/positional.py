import torch
import torch.nn as nn
import math
from typing import Tuple, Optional
from .config import NeuralConfig


class SinusoidalPositionalEncoding(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.max_seq_len = config.max_seq_len
        self.d_model = config.d_model

        pe = torch.zeros(config.max_seq_len, config.d_model)
        position = torch.arange(0, config.max_seq_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, config.d_model, 2).float()
            * (-math.log(10000.0) / config.d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, : x.size(1)]


class LearnedPositionalEncoding(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.pe = nn.Embedding(config.max_seq_len, config.d_model)
        self.max_seq_len = config.max_seq_len

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        positions = torch.arange(
            x.size(1), device=x.device
        ).unsqueeze(0).expand(x.size(0), -1)
        return x + self.pe(positions)


class RotaryPositionalEncoding(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.head_dim = config.head_dim
        self.max_seq_len = config.max_seq_len
        inv_freq = 1.0 / (
            10000
            ** (torch.arange(0, self.head_dim, 2).float() / self.head_dim)
        )
        self.register_buffer("inv_freq", inv_freq)

    def forward(
        self, x: torch.Tensor, seq_len: int, offset: int = 0
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        t = torch.arange(
            offset, offset + seq_len, device=x.device, dtype=self.inv_freq.dtype
        )
        freqs = torch.einsum("i,j->ij", t, self.inv_freq)
        emb = torch.cat((freqs, freqs), dim=-1)
        cos = emb.cos()
        sin = emb.sin()
        return cos, sin


def create_positional_encoding(
    config: NeuralConfig, encoding_type: str = "sinusoidal"
) -> nn.Module:
    if encoding_type == "sinusoidal":
        return SinusoidalPositionalEncoding(config)
    elif encoding_type == "learned":
        return LearnedPositionalEncoding(config)
    elif encoding_type == "rotary":
        return RotaryPositionalEncoding(config)
    else:
        return SinusoidalPositionalEncoding(config)
