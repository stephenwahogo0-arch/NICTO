import torch
import torch.nn.functional as F
import numpy as np
import random
import time
from typing import Dict, List, Optional, Tuple
from ..neural.config import NeuralConfig
from ..neural.elo_system import ELOEstimator
from ..neural.exploration import ExplorationEngine
from ..perception.feature_engine import FeatureEngine

BRAIN_NAMES = ["primary", "analytical", "creative", "strategic", "knowledge", "intuitive"]
DOMAINS = ["general", "code", "math", "creative", "strategic", "knowledge", "intuitive"]
DIFFICULTY_MAP = {
    "general": 1, "code": 3, "math": 4, "creative": 2,
    "strategic": 4, "knowledge": 2, "intuitive": 3,
}


class BrainRouter:
    def __init__(self, config: NeuralConfig, elo_system: ELOEstimator, exploration: ExplorationEngine):
        self.config = config
        self.elo = elo_system
        self.exploration = exploration
        self.feature_engine = FeatureEngine()

        self.curriculum_levels: Dict[str, int] = {brain: 1 for brain in BRAIN_NAMES}
        self.brain_failures: Dict[str, int] = {brain: 0 for brain in BRAIN_NAMES}
        self.routing_history: List[Dict] = []
        self.max_history = 1000

    def route(self, task_vector: np.ndarray, domain: str, curriculum_level: int) -> Dict[str, float]:
        weights = {}
        domain_ratings = []
        for brain in BRAIN_NAMES:
            rating = self.elo.get_rating(brain, domain)
            max_diff = DIFFICULTY_MAP.get(domain, 1)
            brain_level = self.curriculum_levels.get(brain, 1)
            difficulty_ok = curriculum_level <= brain_level + 2
            domain_ratings.append((brain, rating, difficulty_ok))

        max_rating = max(r for _, r, _ in domain_ratings) if domain_ratings else 1500.0
        min_rating = min(r for _, r, _ in domain_ratings) if domain_ratings else 1500.0
        rating_range = max(max_rating - min_rating, 1.0)

        total_weight = 0.0
        for brain, rating, difficulty_ok in domain_ratings:
            if not difficulty_ok:
                weights[brain] = 0.0
                continue
            failure_penalty = max(0.0, 1.0 - self.brain_failures.get(brain, 0) * 0.1)
            normalized = (rating - min_rating) / rating_range
            weight = (0.5 + 0.5 * normalized) * failure_penalty
            weights[brain] = max(0.01, weight)
            total_weight += weight

        if total_weight > 0:
            for brain in weights:
                weights[brain] /= total_weight

        if self.exploration.should_explore("router"):
            explore_brain = random.choice(BRAIN_NAMES)
            weights = {b: 0.0 for b in BRAIN_NAMES}
            weights[explore_brain] = 1.0

        self.routing_history.append({
            "domain": domain,
            "curriculum_level": curriculum_level,
            "weights": dict(weights),
            "timestamp": time.time(),
        })
        if len(self.routing_history) > self.max_history:
            self.routing_history = self.routing_history[-self.max_history:]

        return weights

    def select_brains(self, task: Dict, active_brains: List[str]) -> List[str]:
        feature_vector = self.feature_engine.extract(task)
        domain = task.get("domain", "general")
        curriculum_level = task.get("curriculum_level", 1)
        weights = self.route(feature_vector, domain, curriculum_level)

        sorted_brains = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        selected = []
        cumulative = 0.0
        for brain, weight in sorted_brains:
            if brain in active_brains and weight > 0.05:
                selected.append(brain)
                cumulative += weight
                if cumulative >= 0.85 and len(selected) >= 2:
                    break
        if not selected:
            selected = active_brains[:2] if active_brains else ["primary", "analytical"]

        return selected

    def merge(self,
              brain_outputs: Dict[str, torch.Tensor],
              confidences: Dict[str, torch.Tensor],
              strategy: str = "weighted") -> torch.Tensor:
        if not brain_outputs:
            device = self.config.device
            return torch.zeros(1, 1, self.config.d_model, device=device)

        names = list(brain_outputs.keys())
        tensors = [brain_outputs[n] for n in names]
        B, T, D = tensors[0].shape

        conf_tensors = []
        for name in names:
            if name in confidences:
                c = confidences[name]
                if c.dim() == 3:
                    c = c.mean(dim=-1, keepdim=True)
                while c.dim() < 3:
                    c = c.unsqueeze(-1)
                conf_tensors.append(c.expand(B, T, 1))
            else:
                conf_tensors.append(torch.ones(B, T, 1, device=tensors[0].device) * 0.5)

        stacked_outputs = torch.stack(tensors, dim=2)
        stacked_confs = torch.stack(conf_tensors, dim=2)

        if strategy == "average":
            merged = stacked_outputs.mean(dim=2)

        elif strategy == "max_confidence":
            best_idx = torch.argmax(stacked_confs, dim=2, keepdim=True)
            merged = torch.gather(stacked_outputs, 2, best_idx.expand(-1, -1, -1, D)).squeeze(2)

        else:
            attn_weights = F.softmax(stacked_confs * 2.0, dim=2)
            merged = (stacked_outputs * attn_weights).sum(dim=2)

        return merged

    def update_elo(self, brain: str, domain: str, outcome_score: float, expected: float) -> None:
        expected_clamped = max(0.01, min(0.99, expected))
        won = outcome_score >= expected_clamped
        opponent = 1500.0 + (expected_clamped - 0.5) * 400
        self.elo.update(brain, domain, won, opponent)

        if not won:
            self.brain_failures[brain] = self.brain_failures.get(brain, 0) + 1
        else:
            self.brain_failures[brain] = max(0, self.brain_failures.get(brain, 0) - 1)

    def best_brain_for(self, task: Dict) -> str:
        domain = task.get("domain", "general")
        best, _ = self.elo.best_brain(domain)
        return best

    def domain_specialists(self, domain: str) -> List[Tuple[str, float]]:
        return self.elo.brain_rankings(domain)

    def update_curriculum(self, brain: str, success: bool):
        if success:
            self.curriculum_levels[brain] = min(10, self.curriculum_levels.get(brain, 1) + 1)
        else:
            self.curriculum_levels[brain] = max(1, self.curriculum_levels.get(brain, 1) - 1)

    def routing_stats(self) -> Dict:
        return {
            "curriculum_levels": dict(self.curriculum_levels),
            "brain_failures": dict(self.brain_failures),
            "routing_count": len(self.routing_history),
        }
