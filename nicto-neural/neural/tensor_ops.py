"""Pure PyTorch tensor operations — no high-level nn.Module."""

import math

import torch
import torch.nn.functional as F


def scaled_dot_product(
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    mask: torch.Tensor = None,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Scaled dot-product attention."""
    d_k = q.size(-1)
    scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(d_k)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9)
    attn_weights = F.softmax(scores, dim=-1)
    return torch.matmul(attn_weights, v), attn_weights


def layer_norm(
    x: torch.Tensor,
    weight: torch.Tensor,
    bias: torch.Tensor,
    eps: float = 1e-6,
) -> torch.Tensor:
    """Manual layer normalization."""
    mean = x.mean(-1, keepdim=True)
    std = x.std(-1, keepdim=True)
    return weight * (x - mean) / (std + eps) + bias


def gelu(x: torch.Tensor) -> torch.Tensor:
    """GELU activation."""
    return 0.5 * x * (1 + torch.tanh(
        math.sqrt(2 / math.pi) * (x + 0.044715 * x.pow(3))
    ))


def feed_forward(
    x: torch.Tensor,
    w1: torch.Tensor,
    w2: torch.Tensor,
    b1: torch.Tensor,
    b2: torch.Tensor,
) -> torch.Tensor:
    """Two-layer FFN with GELU."""
    return torch.matmul(gelu(torch.matmul(x, w1) + b1), w2) + b2


def top_k_gating(
    logits: torch.Tensor,
    k: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Top-k gating for MoE."""
    top_k_logits, top_k_indices = torch.topk(logits, k, dim=-1)
    top_k_gates = F.softmax(top_k_logits, dim=-1)
    return top_k_gates, top_k_indices


def elo_expected(rating_a: float, rating_b: float) -> float:
    """ELO expected score."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def elo_update(
    rating: float,
    expected: float,
    actual: float,
    k: int = 32,
) -> float:
    """Standard ELO update."""
    return rating + k * (actual - expected)


def cosine_similarity(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    """Cosine similarity between two tensors."""
    return F.cosine_similarity(a, b, dim=-1)


def temperature_scale(
    logits: torch.Tensor,
    temperature: float = 1.0,
) -> torch.Tensor:
    """Temperature-scaled softmax for confidence calibration."""
    return F.softmax(logits / max(temperature, 1e-8), dim=-1)
