import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Any, Dict, List, Optional, Tuple
from ..neural.config import NeuralConfig


class KnowledgeGate(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.gate = nn.Sequential(
            nn.Linear(d_model * 2, d_model, bias=True),
            nn.Sigmoid(),
        )

    def forward(self, hidden: torch.Tensor, retrieved: torch.Tensor) -> torch.Tensor:
        if retrieved.size(1) != hidden.size(1):
            retrieved = retrieved.mean(dim=1, keepdim=True).expand(-1, hidden.size(1), -1)
        gate = self.gate(torch.cat([hidden, retrieved], dim=-1))
        return gate * retrieved + (1 - gate) * hidden


class CrossAttention(nn.Module):
    def __init__(self, d_model: int, n_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads

        self.q_proj = nn.Linear(d_model, d_model, bias=False)
        self.k_proj = nn.Linear(d_model, d_model, bias=False)
        self.v_proj = nn.Linear(d_model, d_model, bias=False)
        self.out_proj = nn.Linear(d_model, d_model, bias=False)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        B, T, D = x.shape
        _, S, _ = context.shape

        q = self.q_proj(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(context).view(B, S, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(context).view(B, S, self.n_heads, self.head_dim).transpose(1, 2)

        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        attn = F.softmax(scores, dim=-1)
        attn = self.dropout(attn)

        out = torch.matmul(attn, v).transpose(1, 2).contiguous().view(B, T, D)
        out = self.out_proj(out)
        return out


class KnowledgeBrain(nn.Module):
    def __init__(self, config: NeuralConfig, memory_manager=None):
        super().__init__()
        self.config = config
        self.d_model = config.d_model
        self.memory_manager = memory_manager

        self.input_proj = nn.Linear(config.d_model, config.d_model // 2, bias=False)
        self.norm1 = nn.LayerNorm(config.d_model // 2, eps=config.eps)

        self.cross_attn = CrossAttention(config.d_model // 2, n_heads=config.n_heads // 2)

        self.knowledge_ffn = nn.Sequential(
            nn.Linear(config.d_model // 2, config.d_model, bias=True),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model, config.d_model // 2, bias=True),
        )
        self.norm2 = nn.LayerNorm(config.d_model // 2, eps=config.eps)

        self.knowledge_gate = KnowledgeGate(config.d_model // 2)

        self.retrieval_proj = nn.Linear(config.d_model, config.d_model // 2, bias=True)
        self.relevance_proj = nn.Linear(config.d_model // 2, 1, bias=False)

        self.output_proj = nn.Linear(config.d_model // 2, config.d_model, bias=False)
        self.confidence_proj = nn.Linear(config.d_model // 2, 1, bias=False)

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

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        B, T, D = x.shape

        h = self.input_proj(x)
        h = self.norm1(h)

        retrieved = self._default_retrieval(h)
        if retrieved is not None:
            h = self.cross_attn(h, retrieved)
            h = self.knowledge_gate(h, retrieved)

        residual = h
        h = self.knowledge_ffn(h)
        h = self.norm2(h + residual)

        confidence = torch.sigmoid(self.confidence_proj(h))
        out = self.output_proj(h)

        return out, confidence.squeeze(-1)

    def _default_retrieval(self, h: torch.Tensor) -> Optional[torch.Tensor]:
        B, T, D_h = h.shape
        dummy = torch.randn(B, 4, self.d_model, device=h.device)
        return self.retrieval_proj(dummy)

    def retrieve(self, query: str, limit: int = 5) -> List[Dict]:
        results = []
        if self.memory_manager is not None:
            try:
                query_results = self.memory_manager.query(query, limit=limit)
                for store_name, entries in query_results.items():
                    for entry in entries[:limit]:
                        if isinstance(entry, dict):
                            results.append({
                                "store": store_name,
                                "content": entry.get("value", entry.get("content", str(entry))),
                                "relevance": float(entry.get("score", entry.get("relevance", 0.5))),
                            })
                        else:
                            results.append({
                                "store": store_name,
                                "content": str(entry),
                                "relevance": 0.5,
                            })
            except Exception:
                pass
        if not results:
            results.append({
                "store": "builtin",
                "content": f"No specific knowledge found for: {query[:64]}",
                "relevance": 0.1,
            })
        results.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        return results[:limit]

    def augment_with_knowledge(self, x: torch.Tensor, retrieved: List[Dict]) -> torch.Tensor:
        device = x.device
        B, T, D = x.shape

        h = self.input_proj(x)
        h = self.norm1(h)

        context_vectors = []
        for item in retrieved[:4]:
            content_str = str(item.get("content", ""))
            content_hash = abs(hash(content_str)) % 1000 / 1000.0
            ctx = torch.full((1, self.d_model), content_hash, device=device)
            context_vectors.append(ctx)

        if context_vectors:
            ctx_tensor = torch.stack(context_vectors, dim=1)
            ctx_proj = self.retrieval_proj(ctx_tensor)
            ctx_proj = ctx_proj.expand(B, -1, -1)
            h = self.cross_attn(h, ctx_proj)

        h = self.knowledge_ffn(h)
        h = self.norm2(h)
        out = self.output_proj(h)
        return out
