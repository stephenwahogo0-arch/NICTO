import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, List, Optional
from .config import NeuralConfig


class ExpertMLP(nn.Module):
    def __init__(self, config: NeuralConfig, expert_id: int = 0):
        super().__init__()
        self.w1 = nn.Linear(config.d_model, config.d_ff, bias=False)
        self.w2 = nn.Linear(config.d_ff, config.d_model, bias=False)
        self.w3 = nn.Linear(config.d_model, config.d_ff, bias=False)
        self.expert_id = expert_id

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.w2(torch.sigmoid(self.w1(x)) * self.w3(x))


class MoERouter(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.n_experts = config.n_experts
        self.top_k = config.top_k
        self.expert_capacity = config.expert_capacity

        self.gate = nn.Linear(config.d_model, config.n_experts, bias=False)
        self.experts = nn.ModuleList(
            [ExpertMLP(config, i) for i in range(config.n_experts)]
        )

        self.load_balancing_loss = 0.0

    def _top_k_gating(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        logits = self.gate(x)
        gates = F.softmax(logits, dim=-1)
        top_k_gates, top_k_indices = torch.topk(gates, self.top_k, dim=-1)
        top_k_gates = top_k_gates / (top_k_gates.sum(dim=-1, keepdim=True) + 1e-6)
        return gates, top_k_gates, top_k_indices

    def _compute_load_balancing_loss(self, gates: torch.Tensor, top_k_indices: torch.Tensor) -> torch.Tensor:
        tokens_per_expert = torch.zeros(self.n_experts, device=gates.device)
        flat_indices = top_k_indices.view(-1)
        for i in range(self.n_experts):
            tokens_per_expert[i] = (flat_indices == i).float().sum()
        router_z_loss = torch.mean(gates.logsumexp(dim=-1) ** 2)
        load_balancing = torch.var(tokens_per_expert / (tokens_per_expert.sum() + 1e-6))
        return load_balancing + 0.01 * router_z_loss

    def forward(
        self, x: torch.Tensor, return_weights: bool = False
    ) -> torch.Tensor:
        B, T, D = x.shape
        x_flat = x.view(-1, D)

        gates, top_k_gates, top_k_indices = self._top_k_gating(x_flat)
        self.load_balancing_loss = self._compute_load_balancing_loss(gates, top_k_indices)

        routed_out = torch.zeros_like(x_flat)
        expert_weights = torch.zeros_like(x_flat)

        for expert_idx, expert in enumerate(self.experts):
            mask = (top_k_indices == expert_idx).any(dim=-1)
            if mask.any():
                expert_input = x_flat[mask]
                expert_output = expert(expert_input)
                gate_weights = top_k_gates[mask][top_k_indices[mask] == expert_idx]
                if gate_weights.dim() > 1 and gate_weights.size(1) > 1:
                    gate_weights = gate_weights.sum(dim=-1, keepdim=True)
                routed_out[mask] += expert_output * gate_weights
                expert_weights[mask] += gate_weights

        output = routed_out.view(B, T, D)
        weights = expert_weights.view(B, T, D)

        if return_weights:
            return output, weights, top_k_indices.view(B, T, self.top_k)
        return output


class MoETransformerBlock(nn.Module):
    def __init__(self, config: NeuralConfig, layer_idx: int = 0):
        super().__init__()
        from .attention import CausalSelfAttention
        self.ln1 = nn.LayerNorm(config.d_model, eps=config.eps)
        self.attn = CausalSelfAttention(config)
        self.ln2 = nn.LayerNorm(config.d_model, eps=config.eps)
        self.moe = MoERouter(config)
        self.dropout = nn.Dropout(config.dropout)
        self.layer_idx = layer_idx

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        kv_cache: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
    ) -> torch.Tensor:
        x = x + self.dropout(self.attn(self.ln1(x), mask=mask, kv_cache=kv_cache))
        x = x + self.dropout(self.moe(self.ln2(x)))
        return x
