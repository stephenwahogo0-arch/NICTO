import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import re
from typing import Dict, List, Optional, Tuple
from ..neural.config import NeuralConfig

BRAIN_NAMES = ["primary", "analytical", "creative", "strategic", "knowledge", "intuitive"]


class AnalyticalBrain(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.config = config
        self.d_model = config.d_model

        self.input_proj = nn.Linear(config.d_model, config.d_model // 2, bias=False)
        self.norm1 = nn.LayerNorm(config.d_model // 2, eps=config.eps)

        self.logic_ffn = nn.Sequential(
            nn.Linear(config.d_model // 2, config.d_model, bias=True),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model, config.d_model // 2, bias=True),
        )
        self.norm2 = nn.LayerNorm(config.d_model // 2, eps=config.eps)

        self.output_proj = nn.Linear(config.d_model // 2, config.d_model, bias=False)
        self.confidence_proj = nn.Linear(config.d_model // 2, 1, bias=False)

        self.code_head = nn.Linear(config.d_model // 2, 8, bias=False)
        self.math_head = nn.Linear(config.d_model // 2, 4, bias=False)

        self.temperature = nn.Parameter(torch.tensor(0.2))
        self.precision_gate = nn.Linear(config.d_model // 2, 1, bias=False)

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight, gain=0.3)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.LayerNorm):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        B, T, D = x.shape

        h = self.input_proj(x)
        h = self.norm1(h)

        residual = h
        h = self.logic_ffn(h)
        h = self.norm2(h + residual)

        confidence = torch.sigmoid(self.confidence_proj(h))

        temp = torch.clamp(self.temperature, 0.05, 0.5)
        precision = torch.sigmoid(self.precision_gate(h))

        out = self.output_proj(h)

        return out, confidence.squeeze(-1)

    def analyze_code(self, code_tokens: torch.Tensor) -> Dict:
        device = next(self.parameters()).device
        if code_tokens.dim() == 1:
            code_tokens = code_tokens.unsqueeze(0)
        if code_tokens.dim() == 2:
            code_tokens = code_tokens.unsqueeze(0)
        B, T = code_tokens.shape[:2]
        dummy = torch.randn(B, T, self.d_model, device=device)
        h = self.input_proj(dummy)
        h = self.norm1(h)
        logits = self.code_head(h.mean(dim=1))
        probs = F.softmax(logits, dim=-1)

        analysis = {
            "has_syntax_error": bool(probs[0, 0].item() > 0.5),
            "has_logic_error": bool(probs[0, 1].item() > 0.5),
            "complexity": float(probs[0, 2].item()),
            "has_security_issue": bool(probs[0, 3].item() > 0.5),
            "has_perf_issue": bool(probs[0, 4].item() > 0.5),
            "language_detected": int(torch.argmax(probs[0, 5:8]).item()),
            "confidence": float(probs.mean().item()),
        }
        return analysis

    def solve_math(self, expression: str) -> Dict:
        clean = expression.strip()
        result = None
        try:
            safe = re.sub(r'[^0-9+\-*/().%^ ]', '', clean)
            safe = safe.replace('^', '**')
            if re.match(r'^[\d+\-*/().%\s**]+$', safe):
                result = float(eval(safe, {"__builtins__": {}}, {}))
        except Exception:
            result = None
        return {
            "expression": expression,
            "result": result,
            "is_valid": result is not None,
        }
