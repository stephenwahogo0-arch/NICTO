import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional, Tuple, List, Dict
from .super_config import SuperConfig


class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__(); self.eps = eps; self.weight = nn.Parameter(torch.ones(dim))
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps) * self.weight


def precompute_rope(dim, max_len, theta=10000.0):
    freqs = 1.0 / (theta ** (torch.arange(0, dim, 2).float() / dim))
    t = torch.arange(max_len).float()
    angles = torch.outer(t, freqs)
    return torch.cos(angles), torch.sin(angles)


# ============================================================
# 1. MULTI-HEAD LATENT ATTENTION (MLA) — DeepSeek V2/V3 style
# ============================================================
class MultiHeadLatentAttention(nn.Module):
    """Compressed KV latent attention — dramatically reduces KV cache.
    Down-projects K,V into low-rank latent, up-projects at compute time.
    """
    def __init__(self, config: SuperConfig):
        super().__init__()
        D, H, KV = config.d_model, config.n_heads, config.n_kv_heads
        self.hd = config.head_dim
        self.H, self.KV = H, KV
        self.n_rep = H // KV
        self.d_latent = max(64, int(D * config.mla_compression_ratio))
        self.d_latent_kv = max(32, self.d_latent // 2)

        self.q_proj = nn.Linear(D, H * self.hd, bias=False)
        self.kv_down = nn.Linear(D, self.d_latent_kv, bias=False)
        self.q_down = nn.Linear(D, self.d_latent, bias=False) if config.mla_separate_q else None
        self.q_up = nn.Linear(self.d_latent, H * self.hd, bias=False) if self.q_down is not None else None
        self.k_up = nn.Linear(self.d_latent_kv, KV * self.hd, bias=False)
        self.v_up = nn.Linear(self.d_latent_kv, KV * self.hd, bias=False)
        self.o_proj = nn.Linear(H * self.hd, D, bias=False)
        self.drop = nn.Dropout(config.dropout)
        self.scale = self.hd ** -0.5

        self.kv_cache = None

    def _repeat_kv(self, x):
        if self.n_rep == 1: return x
        B, T, H, D = x.shape
        return x[:, :, :, None, :].expand(B, T, H, self.n_rep, D).reshape(B, T, H * self.n_rep, D)

    def forward(self, x, mask=None, cos=None, sin=None):
        B, T, D = x.shape
        q = self.q_proj(x).view(B, T, self.H, self.hd)
        kv_latent = self.kv_down(x)
        k = self.k_up(kv_latent).view(B, T, self.KV, self.hd)
        v = self.v_up(kv_latent).view(B, T, self.KV, self.hd)

        if cos is not None and sin is not None:
            hh = self.hd // 2
            q1, q2 = q[..., :hh], q[..., hh:]
            k1, k2 = k[..., :hh], k[..., hh:]
            cos_t = cos[:T].unsqueeze(0).unsqueeze(2)
            sin_t = sin[:T].unsqueeze(0).unsqueeze(2)
            q = torch.cat([q1*cos_t - q2*sin_t, q1*sin_t + q2*cos_t], -1)
            k = torch.cat([k1*cos_t - k2*sin_t, k1*sin_t + k2*cos_t], -1)

        if self.kv_cache is not None:
            k_cache, v_cache = self.kv_cache
            k = torch.cat([k_cache, k], dim=1)
            v = torch.cat([v_cache, v], dim=1)
        self.kv_cache = (k.detach(), v.detach())

        k = self._repeat_kv(k)
        v = self._repeat_kv(v)

        q, k, v = q.transpose(1,2), k.transpose(1,2), v.transpose(1,2)
        attn = (q @ k.transpose(-2,-1)) * self.scale
        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))
        attn = F.softmax(attn, dim=-1, dtype=torch.float32).to(x.dtype)
        attn = self.drop(attn)
        out = (attn @ v).transpose(1,2).contiguous().view(B, T, D)
        return self.o_proj(out)


# ============================================================
# 2. ENHANCED MoE — Shared experts + fine-grained routing
# ============================================================
class SwiGLU(nn.Module):
    def forward(self, x):
        gate, up = x.chunk(2, dim=-1)
        return F.silu(gate) * up


class FineGrainedExpert(nn.Module):
    def __init__(self, D, FF): super().__init__(); self.w1 = nn.Linear(D, FF, bias=False); self.w2 = nn.Linear(FF, D, bias=False); self.w3 = nn.Linear(D, FF, bias=False)
    def forward(self, x): return self.w2(F.silu(self.w1(x)) * self.w3(x))


class EnhancedMoE(nn.Module):
    """DeepSeek-style MoE with shared experts + fine-grained experts + load balancing."""
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.n_experts = config.n_experts
        self.top_k = config.n_active_experts
        self.n_shared = config.n_shared_experts
        self.z_coef = config.moe_z_loss_coef
        self.aux_coef = config.moe_aux_loss_coef

        self.gate = nn.Linear(config.d_model, config.n_experts, bias=False)
        self.experts = nn.ModuleList([FineGrainedExpert(config.d_model, config.d_ff) for _ in range(config.n_experts)])

        self.shared_experts = nn.ModuleList([FineGrainedExpert(config.d_model, config.d_ff) for _ in range(max(1, self.n_shared))])
        self.shared_gate = nn.Linear(config.d_model, max(1, self.n_shared), bias=False) if self.n_shared > 0 else None

    def forward(self, x):
        B, T, D = x.shape
        flat = x.view(-1, D)
        n = flat.size(0)

        logits = self.gate(flat)
        gates = F.softmax(logits, dim=-1, dtype=torch.float32)
        top_gates, top_idx = torch.topk(gates, self.top_k, dim=-1)
        top_gates = top_gates / (top_gates.sum(-1, keepdim=True) + 1e-6)

        # Shared expert
        shared_out = 0
        if self.shared_gate is not None:
            s_gates = torch.sigmoid(self.shared_gate(x))
            for i, se in enumerate(self.shared_experts):
                shared_out += se(x) * s_gates[..., i:i+1]
            shared_out = shared_out / max(1, self.n_shared)

        # Fine-grained routing
        routed = torch.zeros_like(flat)
        for e_idx, expert in enumerate(self.experts):
            mask = (top_idx == e_idx).any(-1)
            if mask.any():
                ids = mask.nonzero(as_tuple=True)[0]
                ew = top_gates[mask] * (top_idx[mask] == e_idx).float()
                routed[ids] += expert(flat[ids]) * ew.sum(-1, keepdim=True)

        # Load balancing loss
        expert_count = torch.zeros(self.n_experts, device=x.device)
        for i in range(self.n_experts): expert_count[i] = (top_idx == i).float().sum()
        f = expert_count / max(n * self.top_k, 1)
        p = gates.mean(dim=0)
        aux_loss = self.n_experts * (f * p).sum()
        z_loss = gates.logsumexp(dim=-1).pow(2).mean()

        self._last_aux = self.aux_coef * aux_loss
        self._last_z = self.z_coef * z_loss

        return routed.view(B, T, D) + shared_out


# ============================================================
# 3. SUPER NETWORK 1: MultiScaleRetention (RetNet style)
# ============================================================
class MultiScaleRetention(nn.Module):
    """Retention mechanism — parallel training + recurrent inference."""
    def __init__(self, config):
        super().__init__()
        D, H = config.d_model, config.n_heads
        self.hd = D // H
        self.H = H
        self.q = nn.Linear(D, D, bias=False)
        self.k = nn.Linear(D, D, bias=False)
        self.v = nn.Linear(D, D, bias=False)
        self.o = nn.Linear(D, D, bias=False)
        gamma = 1 - torch.exp(torch.linspace(math.log(1/32), math.log(1/512), H))
        self.register_buffer('gamma', gamma.unsqueeze(1))
        self.scale = self.hd ** -0.5

    def forward(self, x, mask=None):
        B, T, D = x.shape
        q = self.q(x).view(B, T, self.H, self.hd) * self.scale
        k = self.k(x).view(B, T, self.H, self.hd)
        v = self.v(x).view(B, T, self.H, self.hd)
        q = F.normalize(q, dim=-1); k = F.normalize(k, dim=-1)

        # Parallel
        D_mask = self.gamma[:, None, :] ** torch.arange(T, device=x.device).view(1, -1, 1)
        scores = q @ k.transpose(-2, -1) * D_mask.unsqueeze(0)
        if mask is not None: scores = scores.masked_fill(mask == 0, float('-inf'))
        attn = F.softmax(scores.float(), dim=-1).to(x.dtype)
        out = (attn @ v).transpose(1,2).contiguous().view(B, T, D)
        return self.o(out)


# ============================================================
# 4. SUPER NETWORK 2: GatedCrossModalFusion
# ============================================================
class GatedCrossModalFusion(nn.Module):
    """Gated fusion for multi-modal inputs."""
    def __init__(self, config):
        super().__init__()
        D = config.d_model
        self.gate_a = nn.Linear(D, D); self.gate_b = nn.Linear(D, D)
        self.fusion = nn.Linear(D * 2, D)
        self.norm = RMSNorm(D)

    def forward(self, a, b):
        ga = torch.sigmoid(self.gate_a(a))
        gb = torch.sigmoid(self.gate_b(b))
        fused = self.fusion(torch.cat([a * ga, b * gb], -1))
        return self.norm(fused + a)


# ============================================================
# 5. SUPER NETWORK 3: AdaptiveInferenceTransformer
# ============================================================
class AdaptiveInferenceTransformer(nn.Module):
    """Token-level adaptive compute — halting units decide when to stop."""
    def __init__(self, config):
        super().__init__()
        D, H = config.d_model, config.n_heads
        self.hd = D // H
        self.H = H
        self.qkv = nn.Linear(D, 3 * D, bias=False)
        self.o = nn.Linear(D, D, bias=False)
        self.halt = nn.Linear(D, 1)
        self.halt_bias = nn.Parameter(torch.tensor(0.1))
        self.max_steps = config.adaptive_max_steps
        self.drop = nn.Dropout(config.dropout)

    def forward(self, x, mask=None):
        B, T, D = x.shape
        qkv = self.qkv(x).view(B, T, 3, self.H, self.hd)
        q, k, v = qkv[:,:,0], qkv[:,:,1], qkv[:,:,2]
        q, k, v = q.transpose(1,2), k.transpose(1,2), v.transpose(1,2)
        attn = (q @ k.transpose(-2,-1)) * (self.hd ** -0.5)
        if mask is not None: attn = attn.masked_fill(mask == 0, float('-inf'))
        attn = F.softmax(attn.float(), dim=-1).to(x.dtype)
        attn = self.drop(attn)
        x1 = (attn @ v).transpose(1,2).contiguous().view(B, T, D)
        x1 = self.o(x1)

        # Adaptive compute
        halting = torch.zeros(B, T, 1, device=x.device)
        remaining = torch.ones(B, T, 1, device=x.device)
        n_updates = torch.ones(B, T, 1, device=x.device, dtype=torch.long)
        acc = x1.clone()
        for step in range(1, self.max_steps):
            h = torch.sigmoid(self.halt(acc) + self.halt_bias) * remaining
            halting = halting + h
            remaining = remaining * (1 - h)
            if remaining.max() < 0.01: break
            qkv_s = self.qkv(acc).view(B, T, 3, self.H, self.hd)
            q_s, k_s, v_s = qkv_s[:,:,0], qkv_s[:,:,1], qkv_s[:,:,2]
            q_s, k_s, v_s = q_s.transpose(1,2), k_s.transpose(1,2), v_s.transpose(1,2)
            attn_s = (q_s @ k_s.transpose(-2,-1)) * (self.hd ** -0.5)
            if mask is not None: attn_s = attn_s.masked_fill(mask == 0, float('-inf'))
            attn_s = F.softmax(attn_s.float(), dim=-1).to(x.dtype)
            x_s = self.o((attn_s @ v_s).transpose(1,2).contiguous().view(B, T, D))
            acc = acc + x_s * h
            n_updates = n_updates + (h > 0.01).long()
        return acc / n_updates.float()


# ============================================================
# 6. SUPER NETWORK 4: HierarchicalTokenMerger
# ============================================================
class HierarchicalTokenMerger(nn.Module):
    """Multi-resolution pyramid — merges similar tokens hierarchically."""
    def __init__(self, config):
        super().__init__()
        D = config.d_model
        self.merge_score = nn.Linear(D, 1)
        self.merge_proj = nn.Linear(D * 2, D)
        self.norm = RMSNorm(D)

    def forward(self, x):
        B, T, D = x.shape
        scores = torch.sigmoid(self.merge_score(x)).squeeze(-1)
        merged = []
        i = 0
        while i < T - 1:
            if scores[0, i] > 0.5 and scores[0, i+1] > 0.5 and len(merged) < T // 2:
                m = self.merge_proj(torch.cat([x[:, i:i+1], x[:, i+1:i+2]], -1))
                merged.append(self.norm(m))
                i += 2
            else:
                merged.append(x[:, i:i+1])
                i += 1
        if i < T: merged.append(x[:, i:])
        return torch.cat(merged, dim=1)


# ============================================================
# 7. SUPER NETWORK 5: NeuralTuringMachineController
# ============================================================
class NeuralTuringMachineController(nn.Module):
    """Differentiable external memory with read/write heads."""
    def __init__(self, config):
        super().__init__()
        D = config.d_model
        self.mem_size = config.ntm_memory_size
        self.mem_dim = config.ntm_memory_dim
        self.memory = nn.Parameter(torch.randn(1, self.mem_size, self.mem_dim) * 0.1)
        self.read_head = nn.Linear(D, self.mem_dim)
        self.write_head = nn.Linear(D, self.mem_dim)
        self.erase_head = nn.Linear(D, self.mem_dim)
        self.key_proj = nn.Linear(D, self.mem_dim)
        self.out_proj = nn.Linear(D + self.mem_dim, D)

    def forward(self, x):
        B, T, D = x.shape
        mem = self.memory.expand(B, -1, -1)
        outs = []
        for t in range(T):
            h = x[:, t:t+1]
            key = self.key_proj(h)
            attn = F.softmax(key @ mem.transpose(-2, -1) * (self.mem_dim ** -0.5), dim=-1)
            read = attn @ mem
            write = self.write_head(h)
            erase = torch.sigmoid(self.erase_head(h))
            mem = mem * (1 - attn.transpose(-2, -1) * erase) + attn.transpose(-2, -1) @ write
            outs.append(self.out_proj(torch.cat([h, read], -1)))
        return torch.cat(outs, dim=1)


# ============================================================
# 8. SUPER NETWORK 6: XNet (Hybrid Mamba-Attention)
# ============================================================
class MambaSSMLayer(nn.Module):
    """Simplified Mamba-2 SSM."""
    def __init__(self, D, d_state=16): super().__init__(); self.A = nn.Parameter(torch.randn(D, d_state) * 0.01); self.B = nn.Linear(D, D * d_state, bias=False); self.C = nn.Linear(D, D * d_state, bias=False); self.D = nn.Parameter(torch.ones(D)); self.dt = nn.Linear(D, D, bias=True); self.D_out = nn.Linear(D, D, bias=False); self.d_state = d_state
    def forward(self, x):
        B, T, D = x.shape
        dt = F.softplus(self.dt(x))
        B_m = self.B(x).view(B, T, D, self.d_state)
        C_m = self.C(x).view(B, T, D, self.d_state)
        A = -F.softplus(self.A)
        h = torch.zeros(B, D, self.d_state, device=x.device)
        ys = []
        for t in range(T):
            h = h * torch.exp(dt[:, t:t+1].transpose(-2,-1) * A.unsqueeze(0).unsqueeze(0))
            h = h + dt[:, t:t+1].transpose(-2,-1) * B_m[:, t:t+1].transpose(-2,-1)
            ys.append((h @ C_m[:, t].unsqueeze(-1)).squeeze(-1) + self.D * x[:, t])
        return self.D_out(torch.stack(ys, dim=1))


class XNetHybridBlock(nn.Module):
    """Hybrid Mamba-2 + Sliding Attention."""
    def __init__(self, config):
        super().__init__()
        D, H = config.d_model, config.n_heads
        self.hd = D // H
        self.H = H
        self.ssm = MambaSSMLayer(D, config.ssm_d_state)
        self.q = nn.Linear(D, D, bias=False); self.k = nn.Linear(D, D, bias=False); self.v = nn.Linear(D, D, bias=False)
        self.o = nn.Linear(D, D, bias=False)
        self.gate = nn.Linear(D, 2)
        self.norm1 = RMSNorm(D); self.norm2 = RMSNorm(D)

    def forward(self, x, mask=None):
        s = self.ssm(self.norm1(x))
        B, T, D = x.shape
        q = self.q(x).view(B, T, self.H, self.hd).transpose(1,2)
        k = self.k(x).view(B, T, self.H, self.hd).transpose(1,2)
        v = self.v(x).view(B, T, self.H, self.hd).transpose(1,2)
        attn = (q @ k.transpose(-2,-1)) * (self.hd**-0.5)
        if mask is not None: attn = attn.masked_fill(mask==0, float('-inf'))
        a = (F.softmax(attn.float(), dim=-1).to(x.dtype) @ v).transpose(1,2).contiguous().view(B,T,D)
        a = self.o(a)
        g = F.softmax(self.gate(x.mean(1)), dim=-1)
        return x + g[:,:,None,0] * s + g[:,:,None,1] * a


# ============================================================
# 9. SUPER NETWORK 7: HyperConnectionTransformer
# ============================================================
class HyperConnection(nn.Module):
    """Learned gated shortcut across transformer layers."""
    def __init__(self, D): super().__init__(); self.gate = nn.Linear(D * 2, D); self.norm = RMSNorm(D)
    def forward(self, x, skip): g = torch.sigmoid(self.gate(torch.cat([x, skip], -1))); return self.norm(x * g + skip * (1 - g))


class HyperConnectionLayer(nn.Module):
    """Transformer block with hyper-connection to a previous layer."""
    def __init__(self, config, layer_idx=0, skip_from=0):
        super().__init__()
        D = config.d_model
        self.attn_norm = RMSNorm(D); self.mlp_norm = RMSNorm(D)
        self.qkv = nn.Linear(D, 3*D, bias=False); self.o = nn.Linear(D, D, bias=False)
        self.w1 = nn.Linear(D, config.d_ff, bias=False); self.w2 = nn.Linear(config.d_ff, D, bias=False); self.w3 = nn.Linear(D, config.d_ff, bias=False)
        self.hyper = HyperConnection(D) if layer_idx % 2 == 0 else None
    def forward(self, x, skip=None, cos=None, sin=None):
        xn = self.attn_norm(x)
        qkv = self.qkv(xn).chunk(3, -1)
        # simple dot-product attn
        q, k, v = [t.view(*t.shape[:2], -1, t.shape[-1] // (self.qkv.out_features//3//x.shape[-1]*x.shape[-1]//3)) for t in qkv]
        q, k, v = [t.transpose(1,2) for t in (q,k,v)]
        attn = (q @ k.transpose(-2,-1)) * (q.size(-1)**-0.5)
        a = (F.softmax(attn.float(), dim=-1).to(x.dtype) @ v).transpose(1,2).contiguous().view(*x.shape)
        x = x + self.o(a)
        xn = self.mlp_norm(x)
        x = x + self.w2(F.silu(self.w1(xn)) * self.w3(xn))
        if self.hyper is not None and skip is not None: x = self.hyper(x, skip)
        return x


# ============================================================
# 10. SUPER NETWORK 8: ProgressiveLayerAggregation
# ============================================================
class ProgressiveLayerAggregation(nn.Module):
    """All layers contribute to output via learned aggregation gates."""
    def __init__(self, config):
        super().__init__()
        D = config.d_model
        self.layers = nn.ModuleList([HyperConnectionLayer(config, i) for i in range(config.n_layers)])
        self.agg_gates = nn.Parameter(torch.ones(config.n_layers) / config.n_layers)
        self.out_norm = RMSNorm(D)

    def forward(self, x, cos=None, sin=None):
        outputs = []
        skip = None
        for i, layer in enumerate(self.layers):
            x = layer(x, skip, cos, sin)
            if i == 0: skip = x
            outputs.append(x)
        gates = F.softmax(self.agg_gates, dim=-1)
        out = sum(o * g for o, g in zip(outputs, gates))
        return self.out_norm(out)


# ============================================================
# 11. SUPER NETWORK 9: SparseMixtureOfAttention
# ============================================================
class SparseMixtureOfAttention(nn.Module):
    """Attention over sparse expert KV heads — only attend to relevant heads."""
    def __init__(self, config):
        super().__init__()
        D, H = config.d_model, config.n_heads
        self.hd = D // H
        self.H = H
        self.n_kv_groups = max(2, H // 4)
        self.kv_size = self.n_kv_groups * self.hd
        self.q = nn.Linear(D, D, bias=False)
        self.kv = nn.Linear(D, self.kv_size * 2, bias=False)
        self.o = nn.Linear(D, D, bias=False)
        self.head_router = nn.Linear(D, self.n_kv_groups, bias=False)

    def forward(self, x, mask=None):
        B, T, D = x.shape
        q = self.q(x).view(B, T, self.H, self.hd)
        kv = self.kv(x).view(B, T, self.n_kv_groups, self.hd * 2)
        k, v = kv.chunk(2, -1)
        routes = F.softmax(self.head_router(x.mean(1)), dim=-1)
        top_routes, top_idx = torch.topk(routes, self.n_kv_groups // 2, dim=-1)
        top_routes = top_routes / (top_routes.sum(-1, keepdim=True) + 1e-6)

        q, k, v = q.transpose(1,2), k.transpose(1,2), v.transpose(1,2)
        attn = (q @ k.transpose(-2,-1)) * (self.hd ** -0.5)
        sparsity = torch.zeros_like(attn)
        for b in range(B):
            for gi in range(self.n_kv_groups):
                if gi in top_idx[b]:
                    sparsity[b, :, :, :] = 1
        attn = attn * sparsity
        if mask is not None: attn = attn.masked_fill(mask == 0, float('-inf'))
        attn = F.softmax(attn.float(), dim=-1).to(x.dtype)
        return self.o((attn @ v).transpose(1,2).contiguous().view(B, T, D))


# ============================================================
# 12. SUPER NETWORK 10: SpeculativeVerificationHead
# ============================================================
class SpeculativeVerificationHead(nn.Module):
    """Verifies and accepts/rejects draft tokens from a fast draft model."""
    def __init__(self, config):
        super().__init__()
        D = config.d_model
        self.verifier = nn.Sequential(
            nn.Linear(D * 2, D), RMSNorm(D), nn.Linear(D, D//2),
            nn.GELU(), nn.Linear(D//2, 1), nn.Sigmoid()
        )

    def forward(self, main_hidden, draft_hidden):
        diff = torch.cat([main_hidden, draft_hidden - main_hidden], -1)
        return self.verifier(diff)


# ============================================================
# EXPORT MAP
# ============================================================
ADVANCED_LAYER_MAP = {
    "mla": MultiHeadLatentAttention,
    "enhanced_moe": EnhancedMoE,
    "retention": MultiScaleRetention,
    "gated_fusion": GatedCrossModalFusion,
    "adaptive_inference": AdaptiveInferenceTransformer,
    "hierarchical_merge": HierarchicalTokenMerger,
    "ntm": NeuralTuringMachineController,
    "xnet": XNetHybridBlock,
    "hyper_connection": HyperConnectionLayer,
    "progressive_agg": ProgressiveLayerAggregation,
    "sparse_moa": SparseMixtureOfAttention,
    "speculative_head": SpeculativeVerificationHead,
}
