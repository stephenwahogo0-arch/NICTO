import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import json
import time
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict
from ..neural.config import NeuralConfig


class PlanCache:
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache = OrderedDict()

    def get(self, key: str) -> Optional[Dict]:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key: str, plan: Dict):
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
        self._cache[key] = plan

    def clear(self):
        self._cache.clear()

    def size(self) -> int:
        return len(self._cache)


class GoalAttention(nn.Module):
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

    def forward(self, x: torch.Tensor, goal_embed: torch.Tensor) -> torch.Tensor:
        B, T, D = x.shape
        G = goal_embed.shape[1]

        q = self.q_proj(x).view(B, T, self.n_heads, self.head_dim).transpose(1, 2)
        k = self.k_proj(goal_embed).view(B, G, self.n_heads, self.head_dim).transpose(1, 2)
        v = self.v_proj(goal_embed).view(B, G, self.n_heads, self.head_dim).transpose(1, 2)

        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        attn = F.softmax(scores, dim=-1)
        attn = self.dropout(attn)

        out = torch.matmul(attn, v).transpose(1, 2).contiguous().view(B, T, D)
        out = self.out_proj(out)
        return out


class StrategicBrain(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.config = config
        self.d_model = config.d_model

        self.plan_cache = PlanCache()

        self.input_proj = nn.Linear(config.d_model, config.d_model // 2, bias=False)
        self.norm1 = nn.LayerNorm(config.d_model // 2, eps=config.eps)

        self.goal_attention = GoalAttention(config.d_model // 2, n_heads=config.n_heads // 2)

        self.plan_ffn = nn.Sequential(
            nn.Linear(config.d_model // 2, config.d_model, bias=True),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model, config.d_model // 2, bias=True),
        )
        self.norm2 = nn.LayerNorm(config.d_model // 2, eps=config.eps)

        self.feasibility_head = nn.Sequential(
            nn.Linear(config.d_model // 2, 64, bias=True),
            nn.ReLU(),
            nn.Linear(64, 1, bias=True),
            nn.Sigmoid(),
        )
        self.step_count_head = nn.Linear(config.d_model // 2, 1, bias=False)

        self.output_proj = nn.Linear(config.d_model // 2, config.d_model, bias=False)
        self.confidence_proj = nn.Linear(config.d_model // 2, 1, bias=False)

        self.goal_embed = nn.Parameter(torch.randn(1, 4, config.d_model // 2) * 0.02)

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight, gain=0.7)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.LayerNorm):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        B, T, D = x.shape

        h = self.input_proj(x)
        h = self.norm1(h)

        goal_embed = self.goal_embed.expand(B, -1, -1)
        h = self.goal_attention(h, goal_embed)

        residual = h
        h = self.plan_ffn(h)
        h = self.norm2(h + residual)

        feasibility = self.feasibility_head(h.mean(dim=1))
        step_count = torch.abs(self.step_count_head(h.mean(dim=1))) + 1

        confidence = torch.sigmoid(self.confidence_proj(h))
        out = self.output_proj(h)

        return out, confidence.squeeze(-1)

    def decompose_goal(self, goal: str, max_depth: int = 3) -> Dict:
        device = next(self.parameters()).device
        dummy = torch.randn(1, 8, self.d_model, device=device)
        h = self.input_proj(dummy)
        h = self.norm1(h)
        goal_embed = self.goal_embed.expand(1, -1, -1)
        h = self.goal_attention(h, goal_embed)
        h = self.plan_ffn(h)

        feasibility = float(self.feasibility_head(h.mean(dim=1))[0, 0].item())
        n_steps = max(1, int(torch.abs(self.step_count_head(h.mean(dim=1)))[0, 0].item()) % 10 + 1)

        tree = {
            "goal": goal,
            "feasibility": feasibility,
            "depth": 0,
            "subgoals": [],
        }

        if max_depth > 0:
            for i in range(min(n_steps, max_depth)):
                sub = {
                    "goal": f"{goal} - Step {i+1}",
                    "feasibility": feasibility * (1.0 - i * 0.1),
                    "depth": 1,
                    "subgoals": [],
                }
                if max_depth > 1 and i == 0:
                    for j in range(2):
                        sub["subgoals"].append({
                            "goal": f"{goal} - Step {i+1}.{j+1}",
                            "feasibility": feasibility * (1.0 - (i + j) * 0.05),
                            "depth": 2,
                            "subgoals": [],
                        })
                tree["subgoals"].append(sub)

        cache_key = goal[:64]
        self.plan_cache.put(cache_key, tree)
        return tree

    def evaluate_plan(self, plan: Dict) -> float:
        score = plan.get("feasibility", 0.5)
        depth = plan.get("depth", 0)
        n_subgoals = len(plan.get("subgoals", []))
        completeness = min(1.0, n_subgoals / max(1, 5 - depth))
        coherence = 1.0 - abs(score - 0.5) * 0.5
        return float(score * 0.4 + completeness * 0.35 + coherence * 0.25)
