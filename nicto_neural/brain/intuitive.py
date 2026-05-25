import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import numpy as np
from typing import Dict, List, Optional, Tuple
from ..neural.config import NeuralConfig
from ..neural.elo_system import ELOEstimator

BRAIN_NAMES = ["primary", "analytical", "creative", "strategic", "knowledge", "intuitive"]


class PatternDetector(nn.Module):
    def __init__(self, d_model: int, n_patterns: int = 16):
        super().__init__()
        self.pattern_embeds = nn.Parameter(torch.randn(n_patterns, d_model) * 0.02)
        self.similarity_scale = nn.Parameter(torch.tensor(1.0))

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        B, T, D = x.shape
        x_flat = x.mean(dim=1)
        patterns = self.pattern_embeds.unsqueeze(0).expand(B, -1, -1)
        sim = torch.matmul(x_flat.unsqueeze(1), patterns.transpose(-2, -1)).squeeze(1)
        sim = sim * torch.abs(self.similarity_scale)
        pattern_scores = F.softmax(sim, dim=-1)
        best_pattern = torch.argmax(pattern_scores, dim=-1)
        return pattern_scores, best_pattern


class ConfidenceEstimator(nn.Module):
    def __init__(self, d_model: int):
        super().__init__()
        self.estimator = nn.Sequential(
            nn.Linear(d_model, 64, bias=True),
            nn.ReLU(),
            nn.Linear(64, 32, bias=True),
            nn.ReLU(),
            nn.Linear(32, 1, bias=True),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.estimator(x)


class IntuitiveBrain(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.config = config
        self.d_model = config.d_model

        self.input_proj = nn.Linear(config.d_model, config.d_model // 2, bias=False)
        self.norm1 = nn.LayerNorm(config.d_model // 2, eps=config.eps)

        self.intuition_ffn = nn.Sequential(
            nn.Linear(config.d_model // 2, config.d_model // 2, bias=True),
            nn.ReLU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model // 2, config.d_model // 2, bias=True),
        )
        self.norm2 = nn.LayerNorm(config.d_model // 2, eps=config.eps)

        self.confidence_estimator = ConfidenceEstimator(config.d_model // 2)
        self.pattern_detector = PatternDetector(config.d_model // 2)

        self.ranking_head = nn.Sequential(
            nn.Linear(config.d_model // 2, 32, bias=True),
            nn.ReLU(),
            nn.Linear(32, 1, bias=True),
        )

        self.brain_classifier = nn.Sequential(
            nn.Linear(config.d_model // 2, 32, bias=True),
            nn.ReLU(),
            nn.Linear(32, len(BRAIN_NAMES), bias=True),
        )

        self.output_proj = nn.Linear(config.d_model // 2, config.d_model, bias=False)
        self.confidence_proj = nn.Linear(config.d_model // 2, 1, bias=False)

        self.temperature = nn.Parameter(torch.tensor(0.5))

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight, gain=0.8)
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
        h = self.intuition_ffn(h)
        h = self.norm2(h + residual)

        confidence = torch.sigmoid(self.confidence_proj(h))
        out = self.output_proj(h)

        return out, confidence.squeeze(-1)

    def estimate_confidence(self, logits: torch.Tensor) -> torch.Tensor:
        if logits.dim() == 1:
            logits = logits.unsqueeze(0)
        if logits.size(-1) != self.d_model // 2:
            fake_h = torch.randn(logits.size(0), self.d_model // 2, device=logits.device)
            return self.confidence_estimator(fake_h).squeeze(-1)
        return self.confidence_estimator(logits).squeeze(-1)

    def rank_options(self, options: List[Dict]) -> List[Tuple[int, float]]:
        device = next(self.parameters()).device
        scores = []
        for opt in options:
            h = torch.randn(1, self.d_model // 2, device=device)
            score = self.ranking_head(h).item()
            scores.append(score)
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return ranked

    def detect_pattern(self, sequence: torch.Tensor) -> Dict:
        device = next(self.parameters()).device
        if sequence.dim() == 1:
            sequence = sequence.unsqueeze(0).unsqueeze(0)
        elif sequence.dim() == 2:
            sequence = sequence.unsqueeze(0)
        if sequence.size(-1) != self.d_model // 2:
            B, T = sequence.shape[:2]
            dummy = torch.randn(B, T, self.d_model // 2, device=device)
            h = dummy
        else:
            h = sequence

        pattern_scores, best_pattern = self.pattern_detector(h)
        brain_logits = self.brain_classifier(h.mean(dim=1))
        brain_probs = F.softmax(brain_logits, dim=-1)

        return {
            "best_pattern": int(best_pattern[0].item()),
            "pattern_scores": pattern_scores[0].detach().cpu().tolist(),
            "recommended_brain": BRAIN_NAMES[int(torch.argmax(brain_probs[0]).item())],
            "brain_probs": {BRAIN_NAMES[i]: float(brain_probs[0, i].item()) for i in range(len(BRAIN_NAMES))},
            "confidence": float(pattern_scores[0, best_pattern[0]].item()),
        }
