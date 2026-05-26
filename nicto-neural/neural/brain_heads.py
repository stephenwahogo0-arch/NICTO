"""Specialized output heads — one per brain."""

import torch
import torch.nn as nn


class BrainHead(nn.Module):
    """Single specialized output head."""

    def __init__(self, config, brain_name: str):
        super().__init__()
        self.name = brain_name
        self.proj = nn.Linear(config.d_model, config.d_model)
        self.output = nn.Linear(config.d_model, config.vocab_size)
        self.confidence = nn.Linear(config.d_model, 1)
        self.dropout = nn.Dropout(config.dropout)

    def forward(self, x: torch.Tensor) -> dict:
        h = self.dropout(torch.tanh(self.proj(x)))
        logits = self.output(h)
        conf = torch.sigmoid(self.confidence(h.mean(1)))
        return {
            "logits": logits,
            "confidence": conf.squeeze(-1),
            "hidden": h,
        }


class BrainHeads(nn.Module):
    """6 specialized output heads — each brain has its own projection layer."""

    def __init__(self, config):
        super().__init__()
        self.heads = nn.ModuleDict({
            name: BrainHead(config, name)
            for name in config.brain_names
        })

    def forward(self, x: torch.Tensor, active_brains: list = None) -> dict:
        if active_brains is None:
            active_brains = list(self.heads.keys())
        return {
            name: self.heads[name](x)
            for name in active_brains
            if name in self.heads
        }

    def get_head(self, name: str) -> BrainHead:
        return self.heads[name]
