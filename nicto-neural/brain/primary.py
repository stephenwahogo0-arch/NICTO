import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple
from ..neural.config import NeuralConfig

BRAIN_NAMES = ["primary", "analytical", "creative", "strategic", "knowledge", "intuitive"]


class PrimaryBrain(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.config = config
        self.d_model = config.d_model

        self.input_proj = nn.Linear(config.d_model, config.d_model // 2, bias=False)
        self.output_proj = nn.Linear(config.d_model // 2, config.d_model, bias=False)
        self.norm = nn.LayerNorm(config.d_model // 2, eps=config.eps)
        self.confidence_proj = nn.Linear(config.d_model // 2, 1, bias=False)

        self.router_mlp = nn.Sequential(
            nn.Linear(config.d_model, 64, bias=True),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(64, len(BRAIN_NAMES), bias=True),
        )
        self.router_norm = nn.LayerNorm(config.d_model)
        self.router_dropout = nn.Dropout(config.dropout)

        self.task_embedding = nn.Linear(15, config.d_model // 2, bias=False)
        self.gate = nn.Linear(config.d_model // 2 * 2, config.d_model // 2, bias=False)

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

    def forward(self, x: torch.Tensor, task_type: str = "general") -> Tuple[torch.Tensor, torch.Tensor]:
        B, T, D = x.shape
        h = self.input_proj(x)
        h = self.norm(h)
        h = F.gelu(h)

        out = self.output_proj(h)
        confidence = torch.sigmoid(self.confidence_proj(h))

        return out, confidence.squeeze(-1)

    def route_task(self, task: Dict, feature_vector: np.ndarray) -> Dict[str, float]:
        device = next(self.parameters()).device
        fv = torch.from_numpy(feature_vector).float().to(device)

        task_type = task.get("task_type", "general")
        type_map = {
            "code": "analytical",
            "math": "analytical",
            "reason": "analytical",
            "creative": "creative",
            "design": "creative",
            "plan": "strategic",
            "goal": "strategic",
            "retrieve": "knowledge",
            "recall": "knowledge",
            "intuit": "intuitive",
            "rank": "intuitive",
        }
        primary_bias = type_map.get(task_type, "analytical")
        domain = task.get("domain", "general")
        domain_map = {
            "code": "analytical",
            "math": "analytical",
            "creative": "creative",
            "strategic": "strategic",
            "knowledge": "knowledge",
            "intuitive": "intuitive",
        }
        domain_bias = domain_map.get(domain, "general")

        dummy_x = torch.randn(1, 1, self.d_model, device=device)
        router_input = self.router_norm(dummy_x)
        logits = self.router_mlp(router_input).squeeze(0).squeeze(0)

        bias_vector = torch.zeros(len(BRAIN_NAMES), device=device)
        if primary_bias in BRAIN_NAMES:
            bias_vector[BRAIN_NAMES.index(primary_bias)] += 0.5
        if domain_bias in BRAIN_NAMES:
            bias_vector[BRAIN_NAMES.index(domain_bias)] += 0.5

        logits = logits + bias_vector
        weights = F.softmax(logits, dim=-1)

        return {name: float(weights[i].item()) for i, name in enumerate(BRAIN_NAMES)}
