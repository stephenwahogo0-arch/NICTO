"""Multi-head attention implementation."""

import torch
import torch.nn as nn

from .tensor_ops import scaled_dot_product


class MultiHeadAttention(nn.Module):
    """Multi-head scaled dot-product attention with causal masking support."""

    def __init__(self, config):
        super().__init__()
        self.d_model = config.d_model
        self.n_heads = config.n_heads
        self.d_k = config.d_model // config.n_heads

        self.W_q = nn.Linear(config.d_model, config.d_model)
        self.W_k = nn.Linear(config.d_model, config.d_model)
        self.W_v = nn.Linear(config.d_model, config.d_model)
        self.W_o = nn.Linear(config.d_model, config.d_model)
        self.dropout = nn.Dropout(config.dropout)
        self.attn_weights = None

    def split_heads(self, x: torch.Tensor, batch_size: int) -> torch.Tensor:
        x = x.view(batch_size, -1, self.n_heads, self.d_k)
        return x.transpose(1, 2)

    def forward(
        self,
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        mask: torch.Tensor = None,
    ) -> torch.Tensor:
        batch_size = q.size(0)
        q = self.split_heads(self.W_q(q), batch_size)
        k = self.split_heads(self.W_k(k), batch_size)
        v = self.split_heads(self.W_v(v), batch_size)

        attn_output, self.attn_weights = scaled_dot_product(q, k, v, mask)
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, -1, self.d_model)
        return self.W_o(self.dropout(attn_output))
