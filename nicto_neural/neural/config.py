import torch
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class NeuralConfig:
    d_model: int = 512
    n_heads: int = 8
    n_layers: int = 6
    d_ff: int = 2048
    n_experts: int = 8
    top_k: int = 2
    vocab_size: int = 32768
    max_seq_len: int = 2048
    dropout: float = 0.1
    activation: str = "gelu"
    eps: float = 1e-6
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    dtype: torch.dtype = torch.float32
    use_mixed_precision: bool = False
    gradient_checkpointing: bool = False
    max_batch_size: int = 32
    head_dim: int = 0

    def __post_init__(self):
        if self.head_dim == 0:
            self.head_dim = self.d_model // self.n_heads

    @property
    def expert_capacity(self) -> int:
        return self.max_batch_size * self.max_seq_len // self.n_experts


BASE_CONFIG = NeuralConfig()

SMALL_CONFIG = NeuralConfig(
    d_model=256,
    n_heads=4,
    n_layers=4,
    d_ff=1024,
    n_experts=4,
    top_k=1,
    max_seq_len=1024,
)

LARGE_CONFIG = NeuralConfig(
    d_model=768,
    n_heads=12,
    n_layers=12,
    d_ff=3072,
    n_experts=16,
    top_k=4,
    max_seq_len=4096,
)
