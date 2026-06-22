import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional, Tuple, List, Dict, Callable
from .super_config import SuperConfig


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        rms = torch.sqrt(x.pow(2).mean(-1, keepdim=True) + self.eps)
        return x / rms * self.weight


def precompute_rope_frequencies(dim: int, max_seq_len: int, theta: float = 10000.0,
                                scaling: Optional[dict] = None,
                                device: torch.device = None) -> Tuple[torch.Tensor, torch.Tensor]:
    freqs = 1.0 / (theta ** (torch.arange(0, dim, 2, device=device).float() / dim))
    if scaling and scaling.get("type") == "linear":
        freqs = freqs / scaling.get("factor", 1.0)
    t = torch.arange(max_seq_len, device=device).float()
    angles = torch.outer(t, freqs)
    cos = torch.cos(angles)
    sin = torch.sin(angles)
    return cos, sin


def apply_rope(x: torch.Tensor, cos: torch.Tensor, sin: torch.Tensor) -> torch.Tensor:
    half = x.shape[-1] // 2
    x1 = x[..., :half]
    x2 = x[..., half:]
    cos = cos[:x.shape[-2], :].unsqueeze(0).unsqueeze(0)
    sin = sin[:x.shape[-2], :].unsqueeze(0).unsqueeze(0)
    rotated_x1 = x1 * cos - x2 * sin
    rotated_x2 = x1 * sin + x2 * cos
    return torch.cat([rotated_x1, rotated_x2], dim=-1)


class FlashAttention2(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.d_model = config.d_model
        self.n_heads = config.n_heads
        self.n_kv_heads = config.n_kv_heads
        self.head_dim = config.head_dim
        self.n_rep = self.n_heads // self.n_kv_heads
        self.sliding_window = config.sliding_window_size
        self.use_alibi = config.use_alibi

        self.q_proj = nn.Linear(config.d_model, self.n_heads * self.head_dim, bias=False)
        self.k_proj = nn.Linear(config.d_model, self.n_kv_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(config.d_model, self.n_kv_heads * self.head_dim, bias=False)
        self.o_proj = nn.Linear(self.n_heads * self.head_dim, config.d_model, bias=False)
        self.attn_dropout = nn.Dropout(config.dropout)
        self.resid_dropout = nn.Dropout(config.dropout)
        self.scale = self.head_dim ** -0.5

        if self.use_alibi:
            alibi_slopes = torch.pow(2, -8 / self.n_heads * torch.arange(1, self.n_heads + 1))
            self.register_buffer("alibi_slopes", alibi_slopes)

    def _repeat_kv(self, x: torch.Tensor) -> torch.Tensor:
        if self.n_rep == 1:
            return x
        B, T, H, D = x.shape
        return x[:, :, :, None, :].expand(B, T, H, self.n_rep, D).reshape(B, T, H * self.n_rep, D)

    def forward(
        self, x: torch.Tensor, mask: Optional[torch.Tensor] = None,
        kv_cache: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        cos: Optional[torch.Tensor] = None, sin: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        B, T, _ = x.shape

        q = self.q_proj(x).view(B, T, self.n_heads, self.head_dim)
        k = self.k_proj(x).view(B, T, self.n_kv_heads, self.head_dim)
        v = self.v_proj(x).view(B, T, self.n_kv_heads, self.head_dim)

        if cos is not None and sin is not None:
            q = apply_rope(q, cos, sin)
            k = apply_rope(k, cos, sin)

        if kv_cache is not None:
            k_cache, v_cache = kv_cache
            k = torch.cat([k_cache, k], dim=1)
            v = torch.cat([v_cache, v], dim=1)

        if self.sliding_window > 0:
            seq_len = k.size(1)
            if seq_len > self.sliding_window:
                k = k[:, -self.sliding_window:]
                v = v[:, -self.sliding_window:]

        k = self._repeat_kv(k)
        v = self._repeat_kv(v)

        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)

        attn = (q @ k.transpose(-2, -1)) * self.scale

        if self.use_alibi:
            T_q = q.size(-2)
            T_k = k.size(-2)
            positions = torch.abs(torch.arange(T_q, device=x.device).unsqueeze(1) - torch.arange(T_k, device=x.device).unsqueeze(0))
            alibi_bias = -self.alibi_slopes[:self.n_heads].unsqueeze(1).unsqueeze(2) * positions.unsqueeze(0)
            attn = attn + alibi_bias

        if mask is not None:
            attn = attn.masked_fill(mask == 0, float("-inf"))

        attn = F.softmax(attn, dim=-1, dtype=torch.float32).to(x.dtype)
        attn = self.attn_dropout(attn)

        out = (attn @ v).transpose(1, 2).contiguous().view(B, T, self.d_model)
        out = self.resid_dropout(self.o_proj(out))
        return out


class SwiGLU(nn.Module):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x_gate, x_up = x.chunk(2, dim=-1)
        return F.silu(x_gate) * x_up


class MoEExpert(nn.Module):
    def __init__(self, config: SuperConfig, expert_id: int = 0):
        super().__init__()
        self.w1 = nn.Linear(config.d_model, config.d_ff, bias=False)
        self.w2 = nn.Linear(config.d_ff, config.d_model, bias=False)
        self.w3 = nn.Linear(config.d_model, config.d_ff, bias=False)
        self.expert_id = expert_id

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.w2(F.silu(self.w1(x)) * self.w3(x))


class ExpertChoiceMoE(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.n_experts = config.n_experts
        self.capacity_factor = config.expert_choice_capacity
        self.z_loss_coef = config.moe_z_loss_coef
        self.aux_loss_coef = config.moe_aux_loss_coef

        self.gate = nn.Linear(config.d_model, config.n_experts, bias=False)
        self.experts = nn.ModuleList([MoEExpert(config, i) for i in range(config.n_experts)])

        if config.n_shared_experts > 0:
            self.shared_expert = MoEExpert(config, -1)
            self.shared_gate = nn.Linear(config.d_model, 1, bias=False)
        else:
            self.shared_expert = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, D = x.shape
        x_flat = x.view(-1, D)
        n_tokens = x_flat.size(0)

        scores = torch.softmax(self.gate(x_flat), dim=-1)
        capacity = min(n_tokens, int(n_tokens * self.n_experts * self.capacity_factor / self.n_experts))
        capacity = max(capacity, 2)

        topk_scores, topk_indices = torch.topk(scores, capacity, dim=0)
        topk_scores = torch.softmax(topk_scores, dim=0)

        routed_out = torch.zeros_like(x_flat)
        load = torch.zeros(self.n_experts, device=x.device)

        for expert_idx, expert in enumerate(self.experts):
            selected_tokens = topk_indices[:, expert_idx]
            selected_scores = topk_scores[:, expert_idx]
            valid = selected_tokens < n_tokens
            if valid.any():
                indices = selected_tokens[valid]
                weights = selected_scores[valid].unsqueeze(-1)
                expert_input = x_flat[indices]
                routed_out.index_add_(0, indices, expert(expert_input) * weights)
                load[expert_idx] = indices.size(0)

        output = routed_out.view(B, T, D)

        if self.shared_expert is not None:
            shared_hidden = self.shared_expert(x)
            shared_weight = torch.sigmoid(self.shared_gate(x))
            output = output + shared_hidden * shared_weight

        expert_fraction = load / max(n_tokens, 1)
        router_weight = scores.mean(dim=0)
        load_balancing = self.n_experts * (expert_fraction * router_weight).sum()
        router_z_loss = torch.mean(scores.logsumexp(dim=-1) ** 2)

        self._last_aux_loss = self.aux_loss_coef * load_balancing
        self._last_z_loss = self.z_loss_coef * router_z_loss

        return output


class HierarchicalMoE(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.n_groups = config.n_expert_groups
        self.n_experts_per_group = config.n_experts_per_group
        self.n_active_groups = config.n_active_groups
        self.n_active_experts = config.n_active_group_experts
        self.z_loss_coef = config.moe_z_loss_coef
        self.aux_loss_coef = config.moe_aux_loss_coef

        self.group_gate = nn.Linear(config.d_model, self.n_groups, bias=False)
        self.expert_gates = nn.ModuleList([
            nn.Linear(config.d_model, self.n_experts_per_group, bias=False)
            for _ in range(self.n_groups)
        ])
        self.experts = nn.ModuleList()
        for g in range(self.n_groups):
            for e in range(self.n_experts_per_group):
                self.experts.append(MoEExpert(config, g * self.n_experts_per_group + e))

        if config.n_shared_experts > 0:
            self.shared_expert = MoEExpert(config, -1)
            self.shared_gate = nn.Linear(config.d_model, 1, bias=False)
        else:
            self.shared_expert = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, D = x.shape
        x_flat = x.view(-1, D)

        group_logits = self.group_gate(x_flat)
        group_weights = F.softmax(group_logits, dim=-1, dtype=torch.float32)
        active_group_weights, active_group_indices = torch.topk(group_weights, self.n_active_groups, dim=-1)
        active_group_weights = active_group_weights / (active_group_weights.sum(dim=-1, keepdim=True) + 1e-6)

        total_z_loss = 0.0
        total_load_balancing = 0.0
        routed_out = torch.zeros_like(x_flat)

        for g_idx in range(self.n_groups):
            group_mask = (active_group_indices == g_idx).any(dim=-1)
            if not group_mask.any():
                continue

            group_tokens = x_flat[group_mask]
            expert_logits = self.expert_gates[g_idx](group_tokens)
            expert_weights = F.softmax(expert_logits, dim=-1, dtype=torch.float32)
            top_expert_weights, top_expert_indices = torch.topk(expert_weights, self.n_active_experts, dim=-1)
            top_expert_weights = top_expert_weights / (top_expert_weights.sum(dim=-1, keepdim=True) + 1e-6)

            g_weight = active_group_weights[group_mask].mean(dim=-1, keepdim=True)

            for e_idx in range(self.n_experts_per_group):
                global_idx = g_idx * self.n_experts_per_group + e_idx
                expert_mask = (top_expert_indices == e_idx)
                token_mask = expert_mask.any(dim=-1)
                if token_mask.any():
                    expert_input = group_tokens[token_mask]
                    expert_output = self.experts[global_idx](expert_input)
                    e_positions = expert_mask[token_mask]
                    e_weights = top_expert_weights[token_mask]
                    w = (e_weights * e_positions).sum(dim=-1, keepdim=True) * g_weight[token_mask]
                    idx = group_mask.nonzero()[token_mask]
                    routed_out = routed_out.index_add(0, idx.view(-1), expert_output * w)

            tokens_per_expert = torch.zeros(self.n_experts_per_group, device=x.device)
            flat_e_indices = top_expert_indices.view(-1)
            for i in range(self.n_experts_per_group):
                tokens_per_expert[i] = (flat_e_indices == i).float().sum()
            total_tokens = max(flat_e_indices.numel(), 1)
            expert_fraction = tokens_per_expert / total_tokens
            router_weight = expert_weights.mean(dim=0)
            total_load_balancing += self.n_experts_per_group * (expert_fraction * router_weight).sum()
            total_z_loss += torch.mean(expert_weights.logsumexp(dim=-1) ** 2)

        output = routed_out.view(B, T, D)

        if self.shared_expert is not None:
            shared_hidden = self.shared_expert(x)
            shared_weight = torch.sigmoid(self.shared_gate(x))
            output = output + shared_hidden * shared_weight

        self._last_aux_loss = self.aux_loss_coef * total_load_balancing
        self._last_z_loss = self.z_loss_coef * total_z_loss

        return output


class MoELayer(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.n_experts = config.n_experts
        self.top_k = config.n_active_experts
        self.z_loss_coef = config.moe_z_loss_coef
        self.aux_loss_coef = config.moe_aux_loss_coef

        self.gate = nn.Linear(config.d_model, config.n_experts, bias=False)
        self.experts = nn.ModuleList([MoEExpert(config, i) for i in range(config.n_experts)])

        if config.n_shared_experts > 0:
            self.shared_expert = MoEExpert(config, -1)
            self.shared_gate = nn.Linear(config.d_model, 1, bias=False)
        else:
            self.shared_expert = None
            self.shared_gate = None

    def _top_k_gating(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        logits = self.gate(x)
        gates = F.softmax(logits, dim=-1, dtype=torch.float32)
        top_k_gates, top_k_indices = torch.topk(gates, self.top_k, dim=-1)
        top_k_gates = top_k_gates / (top_k_gates.sum(dim=-1, keepdim=True) + 1e-6)
        return gates, top_k_gates.to(x.dtype), top_k_indices

    def _compute_aux_loss(self, gates: torch.Tensor, top_k_indices: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        tokens_per_expert = torch.zeros(self.n_experts, device=gates.device)
        flat_indices = top_k_indices.view(-1)
        for i in range(self.n_experts):
            tokens_per_expert[i] = (flat_indices == i).float().sum()
        router_z_loss = torch.mean(gates.logsumexp(dim=-1) ** 2)
        total_tokens = flat_indices.numel()
        expert_fraction = tokens_per_expert / max(total_tokens, 1)
        router_weight = gates.mean(dim=0)
        load_balancing = self.n_experts * (expert_fraction * router_weight).sum()
        return router_z_loss, load_balancing

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, D = x.shape
        x_flat = x.view(-1, D)

        gates, top_k_gates, top_k_indices = self._top_k_gating(x_flat)
        router_z_loss, load_balancing = self._compute_aux_loss(gates, top_k_indices)

        routed_out = torch.zeros_like(x_flat)
        for expert_idx, expert in enumerate(self.experts):
            expert_mask = (top_k_indices == expert_idx)
            token_mask = expert_mask.any(dim=-1)
            if token_mask.any():
                expert_input = x_flat[token_mask]
                expert_output = expert(expert_input)
                gate_positions = expert_mask[token_mask]
                token_weights = top_k_gates[token_mask]
                w = (token_weights * gate_positions).sum(dim=-1, keepdim=True)
                routed_out[token_mask] += expert_output * w

        output = routed_out.view(B, T, D)

        if self.shared_expert is not None:
            shared_hidden = self.shared_expert(x)
            shared_weight = torch.sigmoid(self.shared_gate(x))
            output = output + shared_hidden * shared_weight

        self._last_aux_loss = self.aux_loss_coef * load_balancing
        self._last_z_loss = self.z_loss_coef * router_z_loss

        return output


class MixtureOfDepthsRouter(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.router = nn.Linear(config.d_model, 1, bias=False)
        self.capacity_factor = config.mod_capacity_factor
        self.temperature = nn.Parameter(torch.tensor(1.0))

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        B, T, D = x.shape
        scores = torch.sigmoid(self.router(x) * self.temperature).squeeze(-1)

        k = max(2, int(T * self.capacity_factor))
        if T > k:
            threshold = torch.topk(scores, k, dim=-1).values[:, -1:]
            mask = (scores >= threshold).float()
            mask = mask / (mask.sum(dim=-1, keepdim=True) + 1e-6)
        else:
            mask = torch.ones_like(scores) / T

        return mask, scores


class SSM(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.d_model = config.d_model
        self.d_state = config.mamba_d_state
        self.d_conv = config.mamba_d_conv
        self.expand_factor = config.mamba_expand_factor
        self.d_inner = config.d_model * self.expand_factor

        self.in_proj = nn.Linear(config.d_model, self.d_inner * 2, bias=False)
        self.conv1d = nn.Conv1d(self.d_inner, self.d_inner, kernel_size=self.d_conv,
                                padding=self.d_conv - 1, groups=self.d_inner, bias=False)

        self.x_proj = nn.Linear(self.d_inner, self.d_state * 2, bias=False)
        self.dt_proj = nn.Linear(self.d_state, self.d_inner, bias=True)

        A = torch.arange(1, self.d_state + 1).float().unsqueeze(0).repeat(self.d_inner, 1)
        self.A_log = nn.Parameter(torch.log(A))
        self.D = nn.Parameter(torch.ones(self.d_inner))

        self.out_proj = nn.Linear(self.d_inner, config.d_model, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, D = x.shape

        x_proj = self.in_proj(x)
        x_silu, x_conv = x_proj.chunk(2, dim=-1)

        x_conv = x_conv.transpose(-1, -2)
        x_conv = self.conv1d(x_conv)[..., :T]
        x_conv = F.silu(x_conv.transpose(-1, -2))

        delta_rank = self.x_proj(x_conv)
        delta, B_proj = delta_rank.chunk(2, dim=-1)

        delta = F.softplus(self.dt_proj(delta))
        A = -torch.exp(self.A_log)

        h = torch.zeros(B, self.d_inner, self.d_state, device=x.device)
        y = torch.zeros(B, T, self.d_inner, device=x.device)

        for t in range(T):
            h = h * torch.exp(delta[:, t:t+1].transpose(-2, -1) * A.unsqueeze(0))
            h = h + delta[:, t:t+1].transpose(-2, -1) * x_conv[:, t:t+1].unsqueeze(-1) * B_proj[:, t:t+1].unsqueeze(-2)
            y[:, t] = (h @ (self.D.unsqueeze(-1) * h.sum(dim=-1).unsqueeze(-1))).squeeze(-1)

        y = y * F.silu(x_silu)
        out = self.out_proj(y)
        return out


class SuperTransformerBlock(nn.Module):
    def __init__(self, config: SuperConfig, layer_idx: int = 0):
        super().__init__()
        self.config = config
        self.input_norm = RMSNorm(config.d_model, config.eps)
        self.post_attn_norm = RMSNorm(config.d_model, config.eps)

        if config.use_flash_attn:
            self.attn = FlashAttention2(config)
        else:
            from .attention import CausalSelfAttention
            legacy_config = type('LegacyConfig', (), {
                'd_model': config.d_model, 'n_heads': config.n_heads,
                'head_dim': config.head_dim, 'dropout': config.dropout,
                'max_seq_len': config.max_seq_len, 'eps': config.eps,
            })()
            self.attn = CausalSelfAttention(legacy_config)

        if config.use_hierarchical_moe:
            self.moe = HierarchicalMoE(config)
        elif config.use_expert_choice:
            self.moe = ExpertChoiceMoE(config)
        elif config.use_mamba:
            self.moe = SSM(config)
        else:
            self.moe = MoELayer(config)

        self.use_mod = config.use_mod
        if config.use_mod:
            self.mod_router = MixtureOfDepthsRouter(config)

        self.layer_idx = layer_idx

    def forward(
        self, x: torch.Tensor, mask: Optional[torch.Tensor] = None,
        kv_cache: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        cos: Optional[torch.Tensor] = None, sin: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        residual = x
        x = self.input_norm(x)
        if self.config.use_flash_attn:
            x = self.attn(x, mask=mask, kv_cache=kv_cache, cos=cos, sin=sin)
        else:
            x = self.attn(x, mask=mask, kv_cache=kv_cache)
        x = residual + x

        if self.use_mod:
            mod_mask, mod_scores = self.mod_router(x)
            residual = x
            x = self.post_attn_norm(x)
            x = self.moe(x) * mod_mask.unsqueeze(-1)
            x = residual + x
        else:
            residual = x
            x = self.post_attn_norm(x)
            x = self.moe(x)
            x = residual + x
        return x


class DraftModel(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.d_model = config.draft_model_dim
        self.token_embedding = nn.Linear(config.d_model, config.d_model, bias=False)
        self.layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=config.draft_model_dim, nhead=8,
                dim_feedforward=config.draft_model_dim * 4,
                dropout=config.dropout, batch_first=True,
            )
            for _ in range(config.draft_model_layers)
        ])
        self.output_proj = nn.Linear(config.d_model, config.vocab_size, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.token_embedding(x)
        for layer in self.layers:
            h = layer(h)
        return self.output_proj(h)


class QATLinear(nn.Module):
    def __init__(self, in_features: int, out_features: int, bits: int = 8, bias: bool = False):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.bits = bits
        self.weight = nn.Parameter(torch.randn(out_features, in_features) * 0.02)
        if bias:
            self.bias = nn.Parameter(torch.zeros(out_features))
        else:
            self.bias = None
        self.scale = nn.Parameter(torch.ones(1))
        self.zero_point = nn.Parameter(torch.zeros(1))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.training:
            q_max = 2 ** (self.bits - 1) - 1
            q_min = -2 ** (self.bits - 1)
            scale = self.weight.abs().max() / q_max
            q_weight = torch.clamp(torch.round(self.weight / scale), q_min, q_max)
            w_q = q_weight * scale
        else:
            w_q = self.weight
        out = F.linear(x, w_q, self.bias)
        return out


class QATMoEExpert(MoEExpert):
    def __init__(self, config: SuperConfig, expert_id: int = 0):
        super().__init__(config, expert_id)
        if config.use_qat:
            bits = config.qat_bits
            self.w1 = QATLinear(config.d_model, config.d_ff, bits, bias=False)
            self.w2 = QATLinear(config.d_ff, config.d_model, bits, bias=False)
            self.w3 = QATLinear(config.d_model, config.d_ff, bits, bias=False)


class NASArchitecture:
    def __init__(self, config: SuperConfig):
        self.config = config
        self.population = config.nas_population
        self.generations = config.nas_generations
        self.history = []

    def sample_architecture(self) -> dict:
        return {
            "d_model": self.config.d_model * (1 if torch.randn(1).item() > 0 else 2),
            "n_heads": max(4, self.config.n_heads + torch.randint(-4, 5, (1,)).item()),
            "n_layers": max(4, self.config.n_layers + torch.randint(-4, 5, (1,)).item()),
            "d_ff": self.config.d_ff * (1 if torch.randn(1).item() > 0 else 2),
            "n_experts": max(2, self.config.n_experts + torch.randint(-2, 3, (1,)).item()),
            "use_hierarchical_moe": torch.randn(1).item() > 0,
            "use_expert_choice": torch.randn(1).item() > 0,
            "use_mod": torch.randn(1).item() > 0,
        }

    def search(self, model: nn.Module, dummy_input: torch.Tensor, n_trials: int = 5) -> dict:
        best_config = None
        best_score = float("-inf")
        for i in range(n_trials):
            arch = self.sample_architecture()
            score = 0.0
            try:
                out = model(dummy_input)
                loss = out["logits"].norm()
                loss.backward()
                score = -loss.item() / (arch.get("n_layers", 12) * arch.get("d_model", 768))
            except Exception:
                score = float("-inf")
            self.history.append({"architecture": arch, "score": score})
            if score > best_score:
                best_score = score
                best_config = arch
        return {"best_architecture": best_config, "best_score": best_score, "history": self.history}


class SuperNeuralCore(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.config = config

        self.token_embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.dropout = nn.Dropout(config.dropout)

        if config.use_rope:
            self.cos, self.sin = precompute_rope_frequencies(
                config.head_dim, config.max_seq_len, config.rope_theta, config.rope_scaling
            )
        else:
            self.position_embedding = nn.Embedding(config.max_seq_len, config.d_model)
            self.cos = None
            self.sin = None

        self.layers = nn.ModuleList([
            SuperTransformerBlock(config, i) for i in range(config.n_layers)
        ])
        self.final_norm = RMSNorm(config.d_model, config.eps)

        self.output_proj = nn.Linear(config.d_model, config.vocab_size, bias=False)
        self.output_proj.weight = self.token_embedding.weight

        self.draft = DraftModel(config) if config.use_speculative else None
        self.nas = NASArchitecture(config) if config.use_nas else None

        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear) and not isinstance(module, QATLinear):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(
        self, input_ids: torch.Tensor, mask: Optional[torch.Tensor] = None,
        kv_caches: Optional[List[Optional[Tuple[torch.Tensor, torch.Tensor]]]] = None,
        return_hidden_states: bool = False,
        return_layer_outputs: bool = False,
    ) -> Dict[str, torch.Tensor]:
        B, T = input_ids.shape
        x = self.token_embedding(input_ids)
        x = self.dropout(x)

        if not self.config.use_rope:
            positions = torch.arange(T, device=x.device).unsqueeze(0).expand(B, -1)
            x = x + self.position_embedding(positions)

        cos = self.cos.to(x.device) if self.cos is not None else None
        sin = self.sin.to(x.device) if self.sin is not None else None

        layer_outputs = []
        for i, layer in enumerate(self.layers):
            kv_cache = kv_caches[i] if kv_caches is not None else None
            x = layer(x, mask=mask, kv_cache=kv_cache, cos=cos, sin=sin)
            if return_layer_outputs:
                layer_outputs.append(x)

        x = self.final_norm(x)
        logits = self.output_proj(x)

        result = {"logits": logits, "hidden_states": x}
        if return_layer_outputs:
            result["layer_outputs"] = layer_outputs
        return result

    def speculative_generate(
        self, input_ids: torch.Tensor, max_new_tokens: int = 50, temperature: float = 0.8
    ) -> torch.Tensor:
        if self.draft is None:
            return self._greedy_generate(input_ids, max_new_tokens)

        device = input_ids.device
        generated = input_ids.clone()
        lookahead = min(self.config.spec_lookahead, max_new_tokens)

        for _ in range(0, max_new_tokens, lookahead):
            draft_input = generated[:, -self.config.max_seq_len:]
            draft_logits = self.draft(self.token_embedding(draft_input))
            draft_tokens = torch.argmax(draft_logits[:, -lookahead:], dim=-1)

            full_input = torch.cat([generated, draft_tokens], dim=-1)
            full_logits = self.forward(full_input)["logits"]

            n_accepted = 0
            for t in range(lookahead):
                target_logits = full_logits[:, -(lookahead - t):-(lookahead - t - 1)] if t < lookahead - 1 else full_logits[:, -1:]
                draft_prob = F.softmax(draft_logits[:, -(lookahead - t):-(lookahead - t - 1)] if t < lookahead - 1 else draft_logits[:, -1:], dim=-1)
                target_prob = F.softmax(target_logits, dim=-1)
                ratio = target_prob / (draft_prob + 1e-8)
                draft_token = draft_tokens[:, t:t+1]
                r = ratio.gather(-1, draft_token)

                if r.min().item() >= torch.rand(1, device=device).item():
                    n_accepted += 1
                else:
                    target_dist = target_prob.squeeze(1)
                    draft_tokens[:, t:] = torch.multinomial(target_dist, 1)
                    break

            generated = torch.cat([generated, draft_tokens[:, :max(1, n_accepted)]], dim=-1)
            if generated.size(-1) >= input_ids.size(-1) + max_new_tokens:
                break

        return generated[:, :input_ids.size(-1) + max_new_tokens]

    def _greedy_generate(self, input_ids: torch.Tensor, max_new_tokens: int) -> torch.Tensor:
        for _ in range(max_new_tokens):
            out = self.forward(input_ids[:, -self.config.max_seq_len:])
            next_token = out["logits"][:, -1:].argmax(dim=-1)
            input_ids = torch.cat([input_ids, next_token], dim=-1)
        return input_ids

    def get_hidden_states(
        self, input_ids: torch.Tensor, layer_indices: Optional[List[int]] = None,
    ) -> List[torch.Tensor]:
        B, T = input_ids.shape
        x = self.token_embedding(input_ids)
        x = self.dropout(x)

        if not self.config.use_rope:
            positions = torch.arange(T, device=x.device).unsqueeze(0).expand(B, -1)
            x = x + self.position_embedding(positions)

        cos = self.cos.to(x.device) if self.cos is not None else None
        sin = self.sin.to(x.device) if self.sin is not None else None

        if layer_indices is None:
            layer_indices = list(range(len(self.layers)))

        hidden_states = {}
        for i, layer in enumerate(self.layers):
            x = layer(x, cos=cos, sin=sin)
            if i in layer_indices:
                hidden_states[i] = x

        x = self.final_norm(x)
        hidden_states[self.config.n_layers] = x
        return [hidden_states[i] for i in layer_indices]

    def get_num_params(self) -> int:
        return sum(p.numel() for p in self.parameters())
