"""Knowledge brain — RAG retrieval, semantic search, factual recall."""

import torch
import torch.nn as nn


class KnowledgeBrain(nn.Module):
    """Factual recall, research, information synthesis."""

    def __init__(self, config, elo_system):
        super().__init__()
        self.name = "knowledge"
        self.elo = elo_system
        self.specializations = ["retrieval", "synthesis", "facts"]
        self.knowledge_head = nn.Sequential(
            nn.Linear(config.d_model, config.d_model),
            nn.GELU(),
            nn.Linear(config.d_model, config.d_model),
        )
        self.relevance_head = nn.Linear(config.d_model, 1)
        self.confidence_head = nn.Linear(config.d_model, 1)

    def forward(self, x: torch.Tensor) -> dict:
        h = self.knowledge_head(x)
        relevance = torch.sigmoid(self.relevance_head(h.mean(1)))
        confidence = torch.sigmoid(self.confidence_head(h.mean(1)))
        return {
            "output": h,
            "confidence": confidence,
            "relevance": relevance,
            "brain": self.name,
        }
