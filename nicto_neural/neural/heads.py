import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Dict, List, Optional, Tuple
from .super_config import SuperConfig

BRAIN_HEAD_NAMES = [
    "primary", "analytical", "creative", "strategic",
    "knowledge", "intuitive", "ethical", "linguistic", "temporal",
    "retrieval", "emotional", "executive",
]


class CrossAttentionHead(nn.Module):
    def __init__(self, d_model: int, head_dim: int, n_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        self.d_model = d_model
        self.head_dim = head_dim
        max_h = max(1, head_dim // 64) if head_dim >= 64 else 1
        for h in range(min(n_heads, max_h), 0, -1):
            if head_dim % h == 0:
                self.n_heads = h
                break
        self.per_head_dim = head_dim // self.n_heads

        self.q_proj = nn.Linear(d_model, head_dim, bias=False)
        self.k_proj = nn.Linear(d_model, head_dim, bias=False)
        self.v_proj = nn.Linear(d_model, head_dim, bias=False)
        self.o_proj = nn.Linear(head_dim, head_dim, bias=False)
        self.attn_dropout = nn.Dropout(dropout)
        self.scale = (self.per_head_dim) ** -0.5

    def forward(self, x: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        B, T, D = x.shape
        _, S, _ = context.shape
        q = self.q_proj(x).view(B, T, self.n_heads, self.per_head_dim).transpose(1, 2)
        k = self.k_proj(context).view(B, S, self.n_heads, self.per_head_dim).transpose(1, 2)
        v = self.v_proj(context).view(B, S, self.n_heads, self.per_head_dim).transpose(1, 2)
        attn = (q @ k.transpose(-2, -1)) * self.scale
        attn = F.softmax(attn, dim=-1)
        attn = self.attn_dropout(attn)
        out = (attn @ v).transpose(1, 2).contiguous().view(B, T, -1)
        out = self.o_proj(out)
        return out


class SuperHead(nn.Module):
    def __init__(self, config: SuperConfig, head_name: str):
        super().__init__()
        self.name = head_name
        self.d_model = config.d_model
        self.head_dim = config.brain_head_dim

        self.cross_attn = CrossAttentionHead(
            self.d_model, self.head_dim,
            n_heads=max(2, config.n_heads // config.n_brain_heads),
            dropout=config.dropout,
        )
        self.input_norm = nn.LayerNorm(self.head_dim, eps=config.eps)

        self.task_ffn = nn.Sequential(
            nn.Linear(self.head_dim, self.head_dim * 2, bias=True),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(self.head_dim * 2, self.head_dim, bias=True),
        )
        self.ffn_norm = nn.LayerNorm(self.head_dim, eps=config.eps)

        self.output_proj = nn.Linear(self.head_dim, config.d_model, bias=False)
        self.confidence_proj = nn.Sequential(
            nn.Linear(self.head_dim, 64, bias=True),
            nn.ReLU(),
            nn.Linear(64, 1, bias=True),
            nn.Sigmoid(),
        )
        self.specialization_bias = nn.Parameter(torch.zeros(1, 1, self.head_dim))
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight, gain=0.5)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.LayerNorm):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(
        self, backbone_hidden: torch.Tensor, task_embedding: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.cross_attn(backbone_hidden, backbone_hidden)
        h = self.input_norm(h + self.specialization_bias)
        if task_embedding is not None:
            h = h + task_embedding
        residual = h
        h = self.task_ffn(h)
        h = self.ffn_norm(h + residual)
        confidence = self.confidence_proj(h)
        out = self.output_proj(h)
        return out, confidence.squeeze(-1)


class AnalyticalHead(SuperHead):
    def __init__(self, config: SuperConfig, head_name: str = "analytical"):
        super().__init__(config, head_name)
        self.logic_ffn = nn.Sequential(
            nn.Linear(self.head_dim, self.head_dim * 2, bias=True),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(self.head_dim * 2, self.head_dim, bias=True),
        )
        self.precision_gate = nn.Linear(self.head_dim, 1, bias=False)

    def forward(self, backbone_hidden: torch.Tensor, task_embedding: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.cross_attn(backbone_hidden, backbone_hidden)
        h = self.input_norm(h + self.specialization_bias)
        if task_embedding is not None:
            h = h + task_embedding
        residual = h
        h = self.task_ffn(h)
        h = self.ffn_norm(h + residual)
        h = h + self.logic_ffn(h)
        precision = torch.sigmoid(self.precision_gate(h))
        confidence = self.confidence_proj(h) * precision
        out = self.output_proj(h)
        return out, confidence.squeeze(-1)


class CreativeHead(SuperHead):
    def __init__(self, config: SuperConfig, head_name: str = "creative"):
        super().__init__(config, head_name)
        self.divergent_gate = nn.Sequential(
            nn.Linear(self.head_dim, self.head_dim // 4, bias=True),
            nn.ReLU(),
            nn.Linear(self.head_dim // 4, self.head_dim, bias=True),
            nn.Sigmoid(),
        )
        self.noise_scale = nn.Parameter(torch.tensor(0.3))

    def forward(self, backbone_hidden: torch.Tensor, task_embedding: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.cross_attn(backbone_hidden, backbone_hidden)
        h = self.input_norm(h + self.specialization_bias)
        if task_embedding is not None:
            h = h + task_embedding
        residual = h
        h = self.task_ffn(h)
        gate = self.divergent_gate(h)
        noise = torch.randn_like(h) * self.noise_scale
        h = h + noise * gate
        h = self.ffn_norm(h + residual)
        confidence = self.confidence_proj(h)
        out = self.output_proj(h)
        return out, confidence.squeeze(-1)


class KnowledgeHead(SuperHead):
    def __init__(self, config: SuperConfig, head_name: str = "knowledge"):
        super().__init__(config, head_name)
        self.retrieval_gate = nn.Sequential(
            nn.Linear(self.head_dim * 2, self.head_dim, bias=True),
            nn.Sigmoid(),
        )
        self.memory_context = nn.Parameter(torch.randn(1, 8, self.head_dim) * 0.02)
        self.memory_attn = CrossAttentionHead(
            self.head_dim, self.head_dim,
            n_heads=max(2, config.n_heads // config.n_brain_heads),
            dropout=config.dropout,
        )

    def forward(self, backbone_hidden: torch.Tensor, task_embedding: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.cross_attn(backbone_hidden, backbone_hidden)
        h = self.input_norm(h + self.specialization_bias)
        if task_embedding is not None:
            h = h + task_embedding
        B, T, D = h.shape
        memory = self.memory_context.expand(B, -1, -1)
        memory_out = self.memory_attn(h, memory)
        gate = self.retrieval_gate(torch.cat([h, memory_out], dim=-1))
        h = h + memory_out * gate
        residual = h
        h = self.task_ffn(h)
        h = self.ffn_norm(h + residual)
        confidence = self.confidence_proj(h)
        out = self.output_proj(h)
        return out, confidence.squeeze(-1)


class StrategicHead(SuperHead):
    def __init__(self, config: SuperConfig, head_name: str = "strategic"):
        super().__init__(config, head_name)
        self.goal_embed = nn.Parameter(torch.randn(1, 4, self.head_dim) * 0.02)
        self.goal_attn = CrossAttentionHead(self.head_dim, self.head_dim, n_heads=2, dropout=config.dropout)
        self.feasibility_head = nn.Sequential(
            nn.Linear(self.head_dim, 64, bias=True),
            nn.ReLU(),
            nn.Linear(64, 1, bias=True),
            nn.Sigmoid(),
        )

    def forward(self, backbone_hidden: torch.Tensor, task_embedding: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.cross_attn(backbone_hidden, backbone_hidden)
        h = self.input_norm(h + self.specialization_bias)
        if task_embedding is not None:
            h = h + task_embedding
        B = h.shape[0]
        goals = self.goal_embed.expand(B, -1, -1)
        h = self.goal_attn(h, goals)
        residual = h
        h = self.task_ffn(h)
        h = self.ffn_norm(h + residual)
        feasibility = self.feasibility_head(h.mean(dim=1))
        confidence = self.confidence_proj(h)
        out = self.output_proj(h) * feasibility.unsqueeze(-1)
        return out, confidence.squeeze(-1)


class RetrievalAugmentedHead(SuperHead):
    def __init__(self, config: SuperConfig, head_name: str = "retrieval"):
        super().__init__(config, head_name)
        self.query_proj = nn.Linear(self.head_dim, self.head_dim, bias=False)
        self.key_proj = nn.Linear(self.head_dim, self.head_dim, bias=False)
        self.memory_bank = nn.Parameter(torch.randn(64, self.head_dim) * 0.02)
        self.retrieval_gate = nn.Linear(self.head_dim * 2, 1, bias=False)

    def forward(self, backbone_hidden: torch.Tensor, task_embedding: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.cross_attn(backbone_hidden, backbone_hidden)
        h = self.input_norm(h + self.specialization_bias)
        if task_embedding is not None:
            h = h + task_embedding
        query = self.query_proj(h)
        keys = self.key_proj(self.memory_bank.unsqueeze(0))
        scores = torch.matmul(query, keys.transpose(-2, -1)) / math.sqrt(self.head_dim)
        attn_weights = F.softmax(scores, dim=-1)
        retrieved = attn_weights @ self.memory_bank.unsqueeze(0)
        gate = torch.sigmoid(self.retrieval_gate(torch.cat([h, retrieved], dim=-1)))
        h = h + retrieved * gate
        residual = h
        h = self.task_ffn(h)
        h = self.ffn_norm(h + residual)
        confidence = self.confidence_proj(h)
        out = self.output_proj(h)
        return out, confidence.squeeze(-1)


class EmotionalHead(SuperHead):
    def __init__(self, config: SuperConfig, head_name: str = "emotional"):
        super().__init__(config, head_name)
        self.emotion_embed = nn.Parameter(torch.randn(6, self.head_dim) * 0.02)
        self.emotion_classifier = nn.Linear(self.head_dim, 6, bias=False)
        self.emotion_gate = nn.Linear(self.head_dim, 1, bias=False)

    def forward(self, backbone_hidden: torch.Tensor, task_embedding: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.cross_attn(backbone_hidden, backbone_hidden)
        h = self.input_norm(h + self.specialization_bias)
        if task_embedding is not None:
            h = h + task_embedding
        emotion_logits = self.emotion_classifier(h.mean(dim=1))
        emotion_weights = F.softmax(emotion_logits, dim=-1)
        emotion_context = (emotion_weights.unsqueeze(-1) * self.emotion_embed.unsqueeze(0)).sum(dim=1, keepdim=True)
        gate = torch.sigmoid(self.emotion_gate(h))
        h = h + emotion_context * gate
        residual = h
        h = self.task_ffn(h)
        h = self.ffn_norm(h + residual)
        confidence = self.confidence_proj(h)
        out = self.output_proj(h)
        return out, confidence.squeeze(-1)


class ExecutiveHead(SuperHead):
    def __init__(self, config: SuperConfig, head_name: str = "executive"):
        super().__init__(config, head_name)
        self.plan_embed = nn.Parameter(torch.randn(1, 8, self.head_dim) * 0.02)
        self.priority_head = nn.Linear(self.head_dim, 1, bias=False)

    def forward(self, backbone_hidden: torch.Tensor, task_embedding: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.cross_attn(backbone_hidden, backbone_hidden)
        h = self.input_norm(h + self.specialization_bias)
        if task_embedding is not None:
            h = h + task_embedding
        plans = self.plan_embed.expand(h.shape[0], -1, -1)
        plan_attn = torch.matmul(h, plans.transpose(-2, -1)) / math.sqrt(self.head_dim)
        plan_weights = F.softmax(plan_attn, dim=-1)
        plan_context = plan_weights @ plans
        h = h + plan_context * 0.1
        residual = h
        h = self.task_ffn(h)
        h = self.ffn_norm(h + residual)
        priority = torch.sigmoid(self.priority_head(h))
        confidence = self.confidence_proj(h)
        out = self.output_proj(h) * priority
        return out, confidence.squeeze(-1)


HEAD_CLASSES = {
    "primary": SuperHead,
    "analytical": AnalyticalHead,
    "creative": CreativeHead,
    "strategic": StrategicHead,
    "knowledge": KnowledgeHead,
    "intuitive": SuperHead,
    "ethical": SuperHead,
    "linguistic": SuperHead,
    "temporal": SuperHead,
    "retrieval": RetrievalAugmentedHead,
    "emotional": EmotionalHead,
    "executive": ExecutiveHead,
}


class SuperHeadEnsemble(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.config = config
        self.n_heads = config.n_brain_heads

        self.heads = nn.ModuleDict()
        for name in BRAIN_HEAD_NAMES:
            cls = HEAD_CLASSES.get(name, SuperHead)
            self.heads[name] = cls(config, name)

        self.router = nn.Sequential(
            nn.Linear(config.d_model, config.d_model // 2, bias=True),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model // 2, self.n_heads, bias=True),
        )

        self.fusion_proj = nn.Linear(config.d_model, config.d_model, bias=False)
        self.fusion_norm = nn.LayerNorm(config.d_model, eps=config.eps)
        self.task_embedder = nn.Linear(32, config.brain_head_dim, bias=False)

    def forward(
        self, backbone_hidden: torch.Tensor,
        active_heads: Optional[List[str]] = None,
        task_encoding: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        B, T, D = backbone_hidden.shape
        BPE = backbone_hidden.mean(dim=1)
        routing_logits = self.router(BPE)
        routing_weights = F.softmax(routing_logits, dim=-1)

        task_embed = None
        if task_encoding is not None:
            task_embed = self.task_embedder(task_encoding)

        heads_to_use = active_heads or BRAIN_HEAD_NAMES

        head_outputs = {}
        head_confidences = {}
        for name in heads_to_use:
            if name in self.heads:
                h_out, h_conf = self.heads[name](backbone_hidden, task_embed)
                head_outputs[name] = h_out
                head_confidences[name] = h_conf

        fused = self._fuse_outputs(head_outputs, head_confidences, routing_weights)

        return {
            "outputs": head_outputs,
            "confidences": head_confidences,
            "routing_weights": routing_weights,
            "fused": fused,
            "active_heads": heads_to_use,
        }

    def _fuse_outputs(
        self, outputs: Dict[str, torch.Tensor],
        confidences: Dict[str, torch.Tensor],
        routing_weights: torch.Tensor,
    ) -> torch.Tensor:
        B, T, D = next(iter(outputs.values())).shape
        device = next(iter(outputs.values())).device
        weighted_sum = torch.zeros(B, T, D, device=device)
        weight_sum = torch.zeros(B, T, 1, device=device)
        n_route = routing_weights.shape[-1]
        for i, name in enumerate(BRAIN_HEAD_NAMES):
            if name in outputs and i < n_route:
                w = routing_weights[:, None, i:i+1] * confidences[name].unsqueeze(-1)
                weighted_sum = weighted_sum + outputs[name] * w
                weight_sum = weight_sum + w
        fused = weighted_sum / (weight_sum + 1e-8)
        fused = self.fusion_proj(fused)
        fused = self.fusion_norm(fused)
        return fused

    def route_to_heads(self, backbone_hidden: torch.Tensor, top_k: int = 3) -> List[str]:
        BPE = backbone_hidden.mean(dim=1)
        logits = self.router(BPE)
        weights = F.softmax(logits, dim=-1)
        top_indices = torch.topk(weights[0], min(top_k, self.n_heads)).indices
        top_names = [BRAIN_HEAD_NAMES[i] for i in top_indices]
        return top_names
