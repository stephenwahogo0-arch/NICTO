"""Mixture-of-Experts router with top-k gating and load balancing."""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .tensor_ops import top_k_gating


class Expert(nn.Module):
    """Single expert: two-layer FFN with GELU."""

    def __init__(self, d_model: int, d_ff: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Linear(d_ff, d_model),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class MoERouter(nn.Module):
    """Mixture-of-Experts with top-k gating and load balancing loss."""

    def __init__(self, config):
        super().__init__()
        self.n_experts = config.n_experts
        self.top_k = config.top_k_experts
        self.gate = nn.Linear(config.d_model, config.n_experts)
        self.experts = nn.ModuleList([
            Expert(config.d_model, config.d_ff)
            for _ in range(config.n_experts)
        ])

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        gate_logits = self.gate(x)
        top_k_gates, top_k_indices = top_k_gating(gate_logits, self.top_k)

        output = torch.zeros_like(x)
        for i, expert in enumerate(self.experts):
            mask = (top_k_indices == i).any(dim=-1)
            if mask.any():
                expert_input = x[mask]
                expert_output = expert(expert_input)
                gate_vals = top_k_gates[mask]
                idx_match = (top_k_indices[mask] == i).float()
                weight = (gate_vals * idx_match).sum(dim=-1, keepdim=True)
                output[mask] = output[mask] + weight * expert_output

        # Load balancing loss
        gate_probs = F.softmax(gate_logits, dim=-1)
        tokens_per_expert = torch.zeros(self.n_experts, device=x.device)
        for i in range(self.n_experts):
            tokens_per_expert[i] = (top_k_indices == i).any(dim=-1).float().sum()
        tokens_per_expert = tokens_per_expert / max(x.shape[0] * x.shape[1], 1)
        avg_gate = gate_probs.mean(dim=(0, 1))
        load_balance_loss = (tokens_per_expert * avg_gate).sum() * self.n_experts

        return output, load_balance_loss
