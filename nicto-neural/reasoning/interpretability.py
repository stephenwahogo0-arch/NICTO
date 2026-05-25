"""Interpretability engine — decision path transparency scoring."""

import torch


class InterpretabilityEngine:
    """Provides transparency into NICTO's decision-making process."""

    def __init__(self):
        self._explanations: list[dict] = []

    def explain_decision(
        self,
        task: str,
        brains_used: list[str],
        confidences: dict[str, float],
        domain: str,
        reasoning_chain: list[str] = None,
    ) -> dict:
        """Generate human-readable explanation of decision path."""
        primary_brain = max(confidences, key=confidences.get) if confidences else "unknown"

        explanation = {
            "task_summary": task[:100],
            "domain": domain,
            "primary_brain": primary_brain,
            "brains_activated": brains_used,
            "confidence_breakdown": confidences,
            "reasoning_steps": len(reasoning_chain) if reasoning_chain else 0,
            "transparency_score": self._compute_transparency(
                brains_used, confidences, reasoning_chain
            ),
        }

        if reasoning_chain:
            explanation["reasoning_summary"] = reasoning_chain[:5]

        self._explanations.append(explanation)
        return explanation

    def _compute_transparency(
        self,
        brains_used: list[str],
        confidences: dict[str, float],
        reasoning_chain: list[str] = None,
    ) -> float:
        """Score how interpretable the decision is (0-1)."""
        score = 0.0
        if brains_used:
            score += 0.3
        if confidences:
            conf_spread = max(confidences.values()) - min(confidences.values())
            score += 0.3 * min(1.0, conf_spread * 2)
        if reasoning_chain and len(reasoning_chain) >= 2:
            score += 0.4 * min(1.0, len(reasoning_chain) / 5)
        return min(1.0, score)

    def feature_importance(self, features: torch.Tensor) -> dict:
        """Compute feature importance via magnitude."""
        if features.dim() == 0:
            return {}
        magnitudes = features.abs()
        total = magnitudes.sum() + 1e-8
        importance = (magnitudes / total).tolist()
        labels = [
            "task_type", "domain", "complexity", "reasoning_depth",
            "confidence_trajectory", "memory_recalls", "recency",
            "brain_activations", "time_elapsed", "tool_calls",
            "coherence", "exploration", "curriculum", "reward_trajectory",
            "hacking_flag",
        ]
        return {
            labels[i] if i < len(labels) else f"feature_{i}": round(v, 4)
            for i, v in enumerate(importance if isinstance(importance, list) else [importance])
        }

    def get_recent_explanations(self, n: int = 10) -> list[dict]:
        return self._explanations[-n:]

    def average_transparency(self) -> float:
        if not self._explanations:
            return 0.0
        return sum(
            e["transparency_score"] for e in self._explanations
        ) / len(self._explanations)
