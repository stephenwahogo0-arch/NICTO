"""Confidence calibration — temperature-scaled confidence estimation."""

import torch
import torch.nn.functional as F


class ConfidenceCalibrator:
    """Temperature-scaled confidence on softmax."""

    def __init__(self, initial_temperature: float = 1.5):
        self.temperature = initial_temperature
        self._history: list[tuple[float, bool]] = []

    def calibrate(self, logits: torch.Tensor) -> torch.Tensor:
        """Apply temperature scaling to logits for calibrated confidence."""
        return F.softmax(logits / max(self.temperature, 1e-8), dim=-1)

    def get_confidence(self, logits: torch.Tensor) -> float:
        """Get calibrated max confidence from logits."""
        probs = self.calibrate(logits)
        return float(probs.max())

    def update_temperature(self, predictions: list[float], actuals: list[bool]) -> float:
        """Optimize temperature using validation predictions."""
        if not predictions or not actuals:
            return self.temperature

        best_temp = self.temperature
        best_ece = float("inf")

        for temp in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0]:
            ece = self._compute_ece(predictions, actuals, temp)
            if ece < best_ece:
                best_ece = ece
                best_temp = temp

        self.temperature = best_temp
        return best_temp

    def _compute_ece(
        self,
        predictions: list[float],
        actuals: list[bool],
        temperature: float,
    ) -> float:
        """Expected Calibration Error."""
        n_bins = 10
        bins = [[] for _ in range(n_bins)]

        for pred, actual in zip(predictions, actuals):
            scaled = min(pred / max(temperature, 1e-8), 1.0)
            bin_idx = min(int(scaled * n_bins), n_bins - 1)
            bins[bin_idx].append((scaled, float(actual)))

        ece = 0.0
        total = len(predictions)
        for bin_items in bins:
            if not bin_items:
                continue
            avg_conf = sum(p for p, _ in bin_items) / len(bin_items)
            avg_acc = sum(a for _, a in bin_items) / len(bin_items)
            ece += len(bin_items) / total * abs(avg_conf - avg_acc)

        return ece

    def record(self, confidence: float, was_correct: bool) -> None:
        self._history.append((confidence, was_correct))

    def get_stats(self) -> dict:
        if not self._history:
            return {"temperature": self.temperature, "samples": 0}
        return {
            "temperature": self.temperature,
            "samples": len(self._history),
            "avg_confidence": sum(c for c, _ in self._history) / len(self._history),
            "accuracy": sum(1 for _, correct in self._history if correct) / len(self._history),
        }
