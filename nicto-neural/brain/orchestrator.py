"""Brain router — routes tasks to specialist brains using ELO scores."""

import random

import torch
import torch.nn as nn


class BrainRouter(nn.Module):
    """Routes tasks to specialist brains using ELO scores. Curriculum-aware."""

    def __init__(self, config, elo_system, curriculum_manager):
        super().__init__()
        self.config = config
        self.elo = elo_system
        self.curriculum = curriculum_manager
        self.merge_weights = nn.Parameter(
            torch.ones(config.n_brains) / config.n_brains
        )

    def select_brains(
        self,
        domain: str,
        task_type: str,
        n_brains: int = 2,
        use_exploration: bool = False,
    ) -> list[str]:
        """Select N best brains for a domain."""
        eligible = [
            b for b in self.config.brain_names
            if self.curriculum.can_handle(b, domain)
        ]
        if not eligible:
            eligible = list(self.config.brain_names)

        if use_exploration:
            return random.sample(eligible, min(n_brains, len(eligible)))

        ranked = sorted(
            eligible,
            key=lambda b: self.elo.get_rating(b, domain),
            reverse=True,
        )
        return ranked[:n_brains]

    def merge(self, outputs: dict, confidences: dict) -> dict:
        """Weighted merge of brain outputs by confidence."""
        if not outputs:
            return {"output": None, "confidence": 0.0}

        total_conf = sum(confidences.values()) + 1e-8
        merged = None
        avg_conf = 0.0

        for brain_name, output in outputs.items():
            weight = confidences.get(brain_name, 0.5) / total_conf
            if merged is None:
                merged = output * weight
            else:
                if merged.shape == output.shape:
                    merged = merged + output * weight
            avg_conf += weight * confidences.get(brain_name, 0.5)

        return {"output": merged, "confidence": avg_conf}
