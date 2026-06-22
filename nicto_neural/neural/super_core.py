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


def precompute_rope_frequencies(dim: int, max_seq_len: int, theta: float = 10000.0, device: torch.device = None) -> Tuple[torch.Tensor, torch.Tensor]:
    freqs = 1.0 / (theta ** (torch.arange(0, dim, 2, device=device).float() / dim))
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


class GroupedQueryAttention(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.d_model = config.d_model
        self.n_heads = config.n_heads
        self.n_kv_heads = config.n_kv_heads
        self.head_dim = config.head_dim
        self.n_rep = self.n_heads // self.n_kv_heads

        self.q_proj = nn.Linear(config.d_model, self.n_heads * self.head_dim, bias=False)
        self.k_proj = nn.Linear(config.d_model, self.n_kv_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(config.d_model, self.n_kv_heads * self.head_dim, bias=False)
        self.o_proj = nn.Linear(self.n_heads * self.head_dim, config.d_model, bias=False)
        self.attn_dropout = nn.Dropout(config.dropout)
        self.resid_dropout = nn.Dropout(config.dropout)
        self.scale = self.head_dim ** -0.5
        self.use_flash = config.use_flash_attn
        self.cos = None
        self.sin = None

    def _repeat_kv(self, x: torch.Tensor) -> torch.Tensor:
        if self.n_rep == 1:
            return x
        B, T, H, D = x.shape
        return x[:, :, :, None, :].expand(B, T, H, self.n_rep, D).reshape(B, T, H * self.n_rep, D)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        kv_cache: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        cos: Optional[torch.Tensor] = None,
        sin: Optional[torch.Tensor] = None,
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

        k = self._repeat_kv(k)
        v = self._repeat_kv(v)

        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)

        attn = (q @ k.transpose(-2, -1)) * self.scale
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


class SuperTransformerBlock(nn.Module):
    def __init__(self, config: SuperConfig, layer_idx: int = 0):
        super().__init__()
        self.input_norm = RMSNorm(config.d_model, config.eps)
        self.attn = GroupedQueryAttention(config)
        self.post_attn_norm = RMSNorm(config.d_model, config.eps)
        self.moe = MoELayer(config)
        self.layer_idx = layer_idx

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        kv_cache: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
        cos: Optional[torch.Tensor] = None,
        sin: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        residual = x
        x = self.input_norm(x)
        x = self.attn(x, mask=mask, kv_cache=kv_cache, cos=cos, sin=sin)
        x = residual + x

        residual = x
        x = self.post_attn_norm(x)
        x = self.moe(x)
        x = residual + x
        return x


class SuperNeuralCore(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.config = config

        self.token_embedding = nn.Embedding(config.vocab_size, config.d_model)
        self.dropout = nn.Dropout(config.dropout)

        if config.use_rope:
            self.cos, self.sin = precompute_rope_frequencies(
                config.head_dim, config.max_seq_len, config.rope_theta
            )
        else:
            self.position_embedding = nn.Embedding(config.max_seq_len, config.d_model)
            self.cos = None
            self.sin = None

        self.layers = nn.ModuleList(
            [SuperTransformerBlock(config, i) for i in range(config.n_layers)]
        )
        self.final_norm = RMSNorm(config.d_model, config.eps)

        self.output_proj = nn.Linear(config.d_model, config.vocab_size, bias=False)
        self.output_proj.weight = self.token_embedding.weight

        self._init_weights()

    def _init_weights(self):
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(
        self,
        input_ids: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
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

    def get_hidden_states(
        self,
        input_ids: torch.Tensor,
        layer_indices: Optional[List[int]] = None,
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
