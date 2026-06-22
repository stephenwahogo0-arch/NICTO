import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Dict, List, Optional, Tuple
from .super_config import SuperConfig

REASONING_STYLES = [
    "deductive", "inductive", "abductive", "analogical",
    "critical", "creative", "systematic", "intuitive",
    "counterfactual", "procedural", "meta", "causal", "ethical",
]


class ReasoningPath(nn.Module):
    def __init__(self, config: SuperConfig, style_name: str):
        super().__init__()
        self.style = style_name
        self.d_model = config.d_model
        self.hidden_dim = config.d_ff

        self.path_norm = nn.LayerNorm(self.d_model, eps=config.eps)
        self.path_proj = nn.Linear(self.d_model, self.hidden_dim, bias=True)
        if style_name in ("creative",):
            self.path_act = nn.GELU()
        elif style_name in ("critical", "intuitive"):
            self.path_act = nn.ReLU()
        else:
            self.path_act = nn.SiLU()
        self.path_gate = nn.Linear(self.d_model, self.hidden_dim, bias=True)
        self.path_out = nn.Linear(self.hidden_dim, self.d_model, bias=False)
        self.style_bias = nn.Parameter(torch.zeros(1, 1, self.d_model))
        self.dropout = nn.Dropout(config.dropout)
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

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        h = self.path_norm(x)
        h = self.path_proj(h)
        gate = self.path_gate(x)
        h = self.path_act(h) * F.sigmoid(gate)
        h = self.dropout(h)
        h = self.path_out(h)
        h = h + residual + self.style_bias
        return h


class CounterfactualPath(ReasoningPath):
    def __init__(self, config: SuperConfig, style_name: str = "counterfactual"):
        super().__init__(config, style_name)
        self.what_if_proj = nn.Linear(self.d_model, self.d_model, bias=True)
        self.intervention_noise = nn.Parameter(torch.randn(1, 1, self.d_model) * 0.3)
        self.intervention_gate = nn.Linear(self.d_model, 1, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        h = self.path_norm(x)
        intervention = self.what_if_proj(x)
        gate = torch.sigmoid(self.intervention_gate(x))
        intervention = intervention + self.intervention_noise * gate
        h = h + intervention
        h = self.path_proj(h)
        gate = self.path_gate(x)
        h = self.path_act(h) * F.sigmoid(gate + intervention.mean(dim=-1, keepdim=True))
        h = self.dropout(h)
        h = self.path_out(h)
        h = h + residual + self.style_bias
        return h


class ProceduralPath(ReasoningPath):
    def __init__(self, config: SuperConfig, style_name: str = "procedural"):
        super().__init__(config, style_name)
        self.step_embed = nn.Parameter(torch.randn(1, 8, self.d_model) * 0.02)
        self.step_attn = nn.MultiheadAttention(self.d_model, 4, batch_first=True, dropout=config.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        h = self.path_norm(x)
        steps = self.step_embed.expand(x.shape[0], -1, -1)
        h_step, _ = self.step_attn(h, steps, steps)
        h = h + h_step * 0.1
        h = self.path_proj(h)
        gate = self.path_gate(x)
        h = self.path_act(h) * F.sigmoid(gate)
        h = self.dropout(h)
        h = self.path_out(h)
        h = h + residual + self.style_bias
        return h


class MetaPath(ReasoningPath):
    def __init__(self, config: SuperConfig, style_name: str = "meta"):
        super().__init__(config, style_name)
        self.meta_proj = nn.Linear(self.d_model, self.d_model, bias=True)
        self.meta_score = nn.Linear(self.d_model, 1, bias=False)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        residual = x
        h = self.path_norm(x)
        meta_h = self.meta_proj(h)
        scores = torch.sigmoid(self.meta_score(h))
        h = h + meta_h * scores
        h = self.path_proj(h)
        gate = self.path_gate(x)
        h = self.path_act(h) * F.sigmoid(gate)
        h = self.dropout(h)
        h = self.path_out(h)
        h = h + residual + self.style_bias
        return h, scores.squeeze(-1)


class CausalPath(ReasoningPath):
    def __init__(self, config: SuperConfig, style_name: str = "causal"):
        super().__init__(config, style_name)
        self.cause_proj = nn.Linear(self.d_model, self.d_model // 2, bias=True)
        self.effect_proj = nn.Linear(self.d_model, self.d_model // 2, bias=True)
        self.interv_proj = nn.Linear(self.d_model // 2, self.d_model, bias=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        h = self.path_norm(x)
        cause_h = self.cause_proj(h)
        effect_h = self.effect_proj(h)
        cause_effect = torch.bmm(cause_h, effect_h.transpose(-2, -1)) / math.sqrt(self.d_model // 2)
        cause_effect = F.softmax(cause_effect, dim=-1)
        intervention = self.interv_proj(torch.bmm(cause_effect, effect_h))
        h = h + intervention * 0.1
        h = self.path_proj(h)
        gate = self.path_gate(x)
        h = self.path_act(h) * F.sigmoid(gate)
        h = self.dropout(h)
        h = self.path_out(h)
        h = h + residual + self.style_bias
        return h


class EthicalPath(ReasoningPath):
    def __init__(self, config: SuperConfig, style_name: str = "ethical"):
        super().__init__(config, style_name)
        self.value_embed = nn.Parameter(torch.randn(5, self.d_model) * 0.02)
        self.value_proj = nn.Linear(self.d_model, 5, bias=False)
        self.value_gate = nn.Linear(self.d_model, 1, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        h = self.path_norm(x)
        value_logits = self.value_proj(h.mean(dim=1, keepdim=True))
        value_weights = F.softmax(value_logits, dim=-1)
        value_context = torch.matmul(value_weights, self.value_embed.unsqueeze(0))
        gate = torch.sigmoid(self.value_gate(h))
        h = h + value_context * gate
        h = self.path_proj(h)
        gate = self.path_gate(x)
        h = self.path_act(h) * F.sigmoid(gate)
        h = self.dropout(h)
        h = self.path_out(h)
        h = h + residual + self.style_bias
        return h


PATH_CLASSES = {
    "deductive": ReasoningPath,
    "inductive": ReasoningPath,
    "abductive": ReasoningPath,
    "analogical": ReasoningPath,
    "critical": ReasoningPath,
    "creative": ReasoningPath,
    "systematic": ReasoningPath,
    "intuitive": ReasoningPath,
    "counterfactual": CounterfactualPath,
    "procedural": ProceduralPath,
    "meta": MetaPath,
    "causal": CausalPath,
    "ethical": EthicalPath,
}


class ReasoningFusionGate(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.d_model = config.d_model
        self.n_styles = len(REASONING_STYLES)

        self.path_scorer = nn.Linear(config.d_model, 1, bias=False)

    def forward(self, styles: List[torch.Tensor]) -> Dict[str, torch.Tensor]:
        stacked = torch.stack(styles, dim=0)
        S, B, T, D = stacked.shape

        path_scores = self.path_scorer(stacked.mean(dim=2).mean(dim=1))
        gate_weights = F.softmax(path_scores.squeeze(-1), dim=0)
        gate_weights = gate_weights.view(S, 1, 1, 1)
        fused = (stacked * gate_weights).sum(dim=0)
        return {
            "fused": fused,
            "gate_weights": gate_weights.view(S, -1),
            "style_states": stacked,
        }


class MetaEvaluator(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.d_model = config.d_model
        self.evaluator = nn.Sequential(
            nn.Linear(config.d_model, config.d_model // 2, bias=True),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model // 2, 1, bias=True),
        )

    def forward(self, fused: torch.Tensor) -> torch.Tensor:
        score = self.evaluator(fused.mean(dim=1))
        return torch.sigmoid(score)


class MultiHeadedReasoning(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.config = config
        self.d_model = config.d_model
        self.n_styles = len(REASONING_STYLES)

        self.paths = nn.ModuleDict()
        for style in REASONING_STYLES:
            cls = PATH_CLASSES.get(style, ReasoningPath)
            path = cls(config, style)
            self.paths[style] = path

        self.fusion_gate = ReasoningFusionGate(config)
        self.fusion_norm = nn.LayerNorm(config.d_model, eps=config.eps)
        self.fusion_output = nn.Sequential(
            nn.Linear(config.d_model, config.d_model, bias=True),
            nn.Dropout(config.dropout),
            nn.LayerNorm(config.d_model, eps=config.eps),
        )
        self.meta_evaluator = MetaEvaluator(config)

    def forward(
        self, x: torch.Tensor,
        active_styles: Optional[List[str]] = None,
        return_meta: bool = True,
    ) -> Dict:
        styles_to_use = active_styles or REASONING_STYLES

        path_outputs = {}
        path_tensors = []
        for style in styles_to_use:
            if style not in self.paths:
                continue
            out = self.paths[style](x)
            if isinstance(out, tuple):
                path_tensors.append(out[0])
                path_outputs[style] = out[0], out[1]
            else:
                path_tensors.append(out)
                path_outputs[style] = out

        fusion_result = self.fusion_gate(path_tensors)

        fused = fusion_result["fused"]
        fused = self.fusion_norm(x + fused)
        fused = self.fusion_output(fused)

        meta_score = None
        if return_meta:
            meta_score = self.meta_evaluator(fused)

        return {
            "fused": fused,
            "paths": path_outputs,
            "gate_weights": fusion_result["gate_weights"],
            "meta_score": meta_score,
            "active_styles": styles_to_use,
        }
