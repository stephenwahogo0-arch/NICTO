import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Dict, List, Optional, Tuple
from .super_config import SuperConfig

REASONING_STYLES = [
    "deductive", "inductive", "abductive", "analogical",
    "critical", "creative", "systematic", "intuitive",
]


class ReasoningPath(nn.Module):
    def __init__(self, config: SuperConfig, style: str):
        super().__init__()
        self.style = style
        self.d_model = config.d_model
        self.path_dim = config.reasoning_dim

        self.input_proj = nn.Linear(config.d_model, self.path_dim, bias=False)
        self.norm = nn.LayerNorm(self.path_dim, eps=config.eps)

        self.self_attn = nn.MultiheadAttention(
            self.path_dim, num_heads=max(4, config.n_heads // 4),
            dropout=config.dropout, bias=False, batch_first=True,
        )

        self.ffn = nn.Sequential(
            nn.Linear(self.path_dim, self.path_dim * 2, bias=True),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(self.path_dim * 2, self.path_dim, bias=True),
        )
        self.norm2 = nn.LayerNorm(self.path_dim, eps=config.eps)

        self.confidence_proj = nn.Linear(self.path_dim, 1, bias=False)
        self.coherence_proj = nn.Linear(self.path_dim, 1, bias=False)
        self.output_proj = nn.Linear(self.path_dim, config.d_model, bias=False)

        self.style_bias = nn.Parameter(torch.randn(1, 1, self.path_dim) * 0.02)

        style_scale = {
            "deductive": 0.3, "inductive": 0.5, "abductive": 0.6,
            "analogical": 0.7, "critical": 0.4, "creative": 0.9,
            "systematic": 0.3, "intuitive": 0.6,
        }
        self.temperature = nn.Parameter(torch.tensor(style_scale.get(style, 0.5)))

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
        self, x: torch.Tensor, context: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        B, T, D = x.shape

        h = self.input_proj(x) + self.style_bias
        h = self.norm(h)

        attn_out, _ = self.self_attn(h, h, h)
        h = h + attn_out

        residual = h
        h = self.ffn(h)
        h = self.norm2(h + residual)

        confidence = torch.sigmoid(self.confidence_proj(h))
        coherence = torch.sigmoid(self.coherence_proj(h))
        out = self.output_proj(h)

        return {
            "output": out,
            "confidence": confidence.squeeze(-1),
            "coherence": coherence.squeeze(-1),
            "style": self.style,
            "temperature": torch.clamp(self.temperature, 0.1, 1.0),
        }


class ReasoningFusionGate(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.n_styles = len(REASONING_STYLES)
        self.fusion_ffn = nn.Sequential(
            nn.Linear(config.d_model * 2, config.d_model, bias=True),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model, self.n_styles, bias=True),
        )
        self.fusion_norm = nn.LayerNorm(config.d_model, eps=config.eps)

    def forward(
        self, backbone_hidden: torch.Tensor, path_outputs: Dict[str, Dict]
    ) -> Dict[str, torch.Tensor]:
        B, T, D = backbone_hidden.shape

        active = [s for s in REASONING_STYLES if s in path_outputs]
        n_active = len(active)

        style_outputs = torch.stack(
            [path_outputs[s]["output"] for s in active], dim=2
        )
        style_confs_t = torch.stack(
            [path_outputs[s]["confidence"] for s in active], dim=-1
        )

        gate_input = torch.cat([backbone_hidden, style_outputs.mean(dim=2)], dim=-1)
        fusion_weights = F.softmax(self.fusion_ffn(gate_input), dim=-1)

        weighted_sum = torch.zeros_like(backbone_hidden)
        for idx, s in enumerate(active):
            w = fusion_weights[:, :, idx:idx+1] * style_confs_t[:, :, idx:idx+1]
            weighted_sum = weighted_sum + path_outputs[s]["output"] * w

        fused = self.fusion_norm(weighted_sum)
        overall_confidence = style_confs_t.mean(dim=-1)

        return {
            "fused_output": fused,
            "fusion_weights": fusion_weights,
            "overall_confidence": overall_confidence,
            "n_active_paths": n_active,
        }


class MultiHeadedReasoning(nn.Module):
    def __init__(self, config: SuperConfig):
        super().__init__()
        self.config = config
        self.n_styles = len(REASONING_STYLES)

        self.paths = nn.ModuleDict({
            style: ReasoningPath(config, style) for style in REASONING_STYLES
        })
        self.fusion_gate = ReasoningFusionGate(config)
        self.meta_evaluator = nn.Linear(config.d_model, 1, bias=False)

    def forward(
        self,
        backbone_hidden: torch.Tensor,
        active_styles: Optional[List[str]] = None,
        return_all: bool = False,
    ) -> Dict[str, torch.Tensor]:
        styles = active_styles or REASONING_STYLES

        path_outputs = {}
        for style in styles:
            if style in self.paths:
                path_outputs[style] = self.paths[style](backbone_hidden)

        fusion_result = self.fusion_gate(backbone_hidden, path_outputs)

        meta_score = torch.sigmoid(self.meta_evaluator(fusion_result["fused_output"]))

        result = {
            "fused_output": fusion_result["fused_output"],
            "fusion_weights": fusion_result["fusion_weights"],
            "overall_confidence": fusion_result["overall_confidence"],
            "meta_score": meta_score.squeeze(-1),
            "active_styles": styles,
            "n_active_paths": fusion_result["n_active_paths"],
        }

        if return_all:
            result["path_outputs"] = {
                s: {
                    "confidence": path_outputs[s]["confidence"],
                    "coherence": path_outputs[s]["coherence"],
                    "temperature": path_outputs[s]["temperature"],
                }
                for s in styles if s in path_outputs
            }

        return result

    def select_best_styles(
        self, backbone_hidden: torch.Tensor, n_select: int = 3
    ) -> List[str]:
        scores = {}
        for style in REASONING_STYLES:
            out = self.paths[style](backbone_hidden)
            scores[style] = out["confidence"].mean().item()
        sorted_styles = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [s for s, _ in sorted_styles[:n_select]]
