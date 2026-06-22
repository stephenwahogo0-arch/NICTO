import torch
import torch.nn.functional as F
from typing import Optional, Tuple


def batched_matmul(
    a: torch.Tensor, b: torch.Tensor, transpose_b: bool = False
) -> torch.Tensor:
    if transpose_b:
        b = b.transpose(-2, -1)
    return torch.matmul(a, b)


def softmax(
    x: torch.Tensor, dim: int = -1, mask: Optional[torch.Tensor] = None
) -> torch.Tensor:
    if mask is not None:
        x = x.masked_fill(mask == 0, float("-inf"))
    return torch.softmax(x, dim=dim)


def layer_norm(
    x: torch.Tensor,
    weight: torch.Tensor,
    bias: Optional[torch.Tensor] = None,
    eps: float = 1e-6,
) -> torch.Tensor:
    mean = x.mean(dim=-1, keepdim=True)
    var = x.var(dim=-1, keepdim=True, unbiased=False)
    return weight * (x - mean) / torch.sqrt(var + eps) + (bias if bias is not None else 0)


def gelu(x: torch.Tensor) -> torch.Tensor:
    return F.gelu(x)


def silu(x: torch.Tensor) -> torch.Tensor:
    return x * torch.sigmoid(x)


def relu(x: torch.Tensor) -> torch.Tensor:
    return F.relu(x)


def activation_fn(name: str, x: torch.Tensor) -> torch.Tensor:
    if name == "gelu":
        return gelu(x)
    elif name == "silu":
        return silu(x)
    elif name == "relu":
        return relu(x)
    else:
        return gelu(x)


def top_k_gating(
    logits: torch.Tensor, k: int
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    top_k_values, top_k_indices = torch.topk(torch.softmax(logits, dim=-1), k, dim=-1)
    gates = torch.zeros_like(logits)
    gates.scatter_(-1, top_k_indices, top_k_values)
    return gates, top_k_values, top_k_indices


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    x1, x2 = x.chunk(2, dim=-1)
    return torch.cat((-x2, x1), dim=-1)


def apply_rotary_emb(
    x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor
) -> torch.Tensor:
    return (x * cos) + (rotate_half(x) * sin)
