import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Dict, List, Optional, Tuple
from ..neural.config import NeuralConfig


class DivergentThinking(nn.Module):
    def __init__(self, d_model: int, dropout: float = 0.1):
        super().__init__()
        self.noise_gate = nn.Sequential(
            nn.Linear(d_model, d_model // 4, bias=True),
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model, bias=True),
            nn.Sigmoid(),
        )
        self.noise_proj = nn.Linear(d_model, d_model, bias=False)
        self.noise_scale = nn.Parameter(torch.tensor(0.3))

    def forward(self, x: torch.Tensor, temperature: float = 0.8) -> torch.Tensor:
        gate = self.noise_gate(x)
        noise = torch.randn_like(x) * self.noise_scale * temperature
        noise = self.noise_proj(noise)
        return x + noise * gate


class CreativeBrain(nn.Module):
    def __init__(self, config: NeuralConfig):
        super().__init__()
        self.config = config
        self.d_model = config.d_model

        self.input_proj = nn.Linear(config.d_model, config.d_model // 2, bias=False)
        self.norm1 = nn.LayerNorm(config.d_model // 2, eps=config.eps)

        self.associative_ffn = nn.Sequential(
            nn.Linear(config.d_model // 2, config.d_model, bias=True),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model, config.d_model, bias=True),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.d_model, config.d_model // 2, bias=True),
        )
        self.norm2 = nn.LayerNorm(config.d_model // 2, eps=config.eps)

        self.divergent = DivergentThinking(config.d_model // 2, config.dropout)
        self.output_proj = nn.Linear(config.d_model // 2, config.d_model, bias=False)
        self.confidence_proj = nn.Linear(config.d_model // 2, 1, bias=False)

        self.idea_proj = nn.Linear(config.d_model // 2, 32, bias=False)

        self.temperature = nn.Parameter(torch.tensor(0.8))

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight, gain=1.5)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.LayerNorm):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor, temperature: float = 0.8) -> Tuple[torch.Tensor, torch.Tensor]:
        B, T, D = x.shape

        h = self.input_proj(x)
        h = self.norm1(h)

        residual = h
        h = self.associative_ffn(h)
        h = self.norm2(h + residual)

        temp = max(0.5, min(1.2, self.temperature.item() if isinstance(self.temperature, nn.Parameter) else temperature))
        h = self.divergent(h, temperature=temp)

        confidence = torch.sigmoid(self.confidence_proj(h))
        out = self.output_proj(h)

        return out, confidence.squeeze(-1)

    def brainstorm(self, prompt: str, n_ideas: int = 5) -> List[str]:
        device = next(self.parameters()).device
        B, T = 1, n_ideas
        dummy = torch.randn(B, T, self.d_model, device=device)

        h = self.input_proj(dummy)
        h = self.norm1(h)
        h = self.associative_ffn(h)
        h = self.divergent(h, temperature=1.0)

        idea_embeds = self.idea_proj(h)

        ideas = []
        for i in range(n_ideas):
            seed = idea_embeds[0, i].detach().cpu().numpy()
            tags = []
            if seed[0] > 0:
                tags.append("novel")
            if seed[1] > 0:
                tags.append("practical")
            if seed[2] > 0:
                tags.append("elegant")
            if seed[3] > 0:
                tags.append("scalable")
            if not tags:
                tags.append("alternative")
            ideas.append({
                "id": i,
                "tags": tags,
                "diversity_score": float(abs(seed).mean()),
                "prompt": prompt,
            })

        return [
            f"Concept {i+1}: {' '.join(ideas[i]['tags'])} approach for '{prompt}'"
            for i in range(n_ideas)
        ]
