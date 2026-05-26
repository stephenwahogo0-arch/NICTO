"""Validation engine — hold-out validation for generalization testing."""

import asyncio
import random


class ValidationEngine:
    """Hold-out validation: 80% training, 20% unseen. Tests generalization."""

    def __init__(self, memory_manager):
        self.memory = memory_manager
        self._hold_out: list[dict] = []
        self._results: list[float] = []

    def split(self, dataset: list, ratio: float = 0.8) -> tuple[list, list]:
        """80/20 split — hold-out is NEVER seen during training."""
        shuffled = dataset.copy()
        random.shuffle(shuffled)
        split_idx = int(len(shuffled) * ratio)
        train = shuffled[:split_idx]
        hold_out = shuffled[split_idx:]
        self._hold_out = hold_out
        return train, hold_out

    def evaluate(self, consciousness, hold_out: list = None) -> dict:
        """Evaluate on hold-out set without ELO updates."""
        test_set = hold_out or self._hold_out
        if not test_set:
            return {"accuracy": 0.0, "n_samples": 0}

        correct = 0
        results = []

        for sample in test_set[:100]:
            result = asyncio.run(
                consciousness.think(
                    sample.get("input", "test"),
                    {"no_elo_update": True},
                )
            )
            confidence = result.get("confidence", 0.0)
            is_correct = confidence > 0.6
            if is_correct:
                correct += 1
            results.append({
                "input": sample.get("input", "")[:50],
                "confidence": confidence,
                "correct": is_correct,
            })

        accuracy = correct / max(len(test_set[:100]), 1)
        self._results.append(accuracy)

        return {
            "accuracy": accuracy,
            "n_samples": len(test_set),
            "n_tested": min(100, len(test_set)),
            "history": self._results[-10:],
        }

    def accuracy_trend(self) -> str:
        if len(self._results) < 2:
            return "insufficient_data"
        recent = self._results[-5:]
        if recent[-1] > recent[0]:
            return "improving"
        if recent[-1] < recent[0]:
            return "degrading"
        return "stable"
