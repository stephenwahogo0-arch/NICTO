import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple
from .config import NeuralConfig


HEAD_NAMES = ["primary", "analytical", "creative", "strategic", "knowledge", "intuitive"]


class BrainHead(nn.Module):
    def __init__(self, config: NeuralConfig, head_name: str, head_dim: Optional[int] = None):
        super().__init__()
        self.name = head_name
        self.head_dim = head_dim or config.d_model // len(HEAD_NAMES)
        self.d_model = config.d_model

        self.input_proj = nn.Linear(config.d_model, self.head_dim, bias=False)
        self.output_proj = nn.Linear(self.head_dim, config.d_model // 2, bias=False)
        self.confidence_proj = nn.Linear(self.head_dim, 1, bias=False)
        self.specialized_norm = nn.LayerNorm(self.head_dim, eps=config.eps)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        head_input = self.input_proj(x)
        head_input = self.specialized_norm(head_input)
        head_output = self.output_proj(head_input)
        confidence = torch.sigmoid(self.confidence_proj(head_input))
        return head_output, confidence


class BrainHeadEnsemble(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.config = config
        self.heads = nn.ModuleDict({
            name: BrainHead(config, name) for name in HEAD_NAMES
        })
        self.router = nn.Linear(config.d_model, len(HEAD_NAMES), bias=False)
        self.fusion = nn.Linear(config.d_model // 2 * len(HEAD_NAMES), config.d_model, bias=False)

    def forward(
        self,
        x: torch.Tensor,
        active_heads: Optional[List[str]] = None,
    ) -> Dict[str, torch.Tensor]:
        B, T, D = x.shape
        routing_logits = self.router(x.mean(dim=1))

        head_outputs = {}
        head_confidences = {}
        heads_to_use = active_heads or HEAD_NAMES

        for name in heads_to_use:
            if name in self.heads:
                h_out, h_conf = self.heads[name](x)
                head_outputs[name] = h_out
                head_confidences[name] = h_conf

        return {
            "outputs": head_outputs,
            "confidences": head_confidences,
            "routing_logits": routing_logits,
        }

    def merge_outputs(
        self,
        head_outputs: Dict[str, torch.Tensor],
        head_confidences: Dict[str, torch.Tensor],
        routing_weights: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        merged = []
        weights = []

        for name in HEAD_NAMES:
            if name in head_outputs:
                merged.append(head_outputs[name])
                if routing_weights is not None:
                    w = routing_weights[:, :, None] * head_confidences[name]
                else:
                    w = head_confidences[name]
                weights.append(w)

        if not merged:
            return torch.zeros(1, 1, self.config.d_model, device=self.config.device)

        stacked = torch.stack(merged, dim=2)
        weight_stack = torch.stack(weights, dim=2)
        weight_stack = F.softmax(weight_stack, dim=2)

        weighted_sum = (stacked * weight_stack).sum(dim=2)
        B, T, _ = weighted_sum.shape
        out = self.fusion(weighted_sum.view(B, T, -1))
        return out


class SpecializedBrainHead(BrainHead):
    def __init__(self, config: NeuralConfig, head_name: str, head_dim: Optional[int] = None):
        super().__init__(config, head_name, head_dim)
        self.task_bias = nn.Parameter(torch.zeros(1, 1, self.head_dim))

    def forward(self, x: torch.Tensor, task_embedding: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        head_input = self.input_proj(x)
        if task_embedding is not None:
            head_input = head_input + self.task_bias * task_embedding.mean(dim=-1, keepdim=True)
        head_input = self.specialized_norm(head_input)
        head_output = self.output_proj(head_input)
        confidence = torch.sigmoid(self.confidence_proj(head_input))
        return head_output, confidence
