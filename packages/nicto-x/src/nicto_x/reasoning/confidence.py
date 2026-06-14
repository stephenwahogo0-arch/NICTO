"""NICTO X — Calibrated confidence estimation with multi-signal fusion and retry logic."""

from __future__ import annotations

import logging
import math
from typing import Optional

logger = logging.getLogger("nicto_x.reasoning.confidence")


class ConfidenceEstimator:
    """Multi-signal confidence estimator with calibration tracking."""

    def __init__(self):
        self._calibration_data: list[dict] = []

    def estimate(self, output: str, reflection: Optional[dict] = None) -> dict:
        scores = {}

        length_score = min(1.0, len(output) / 300)
        scores["length"] = round(length_score, 3)

        word_count = len(output.split())
        scores["word_count"] = round(min(1.0, word_count / 60), 3)

        unique_words = len(set(w.lower() for w in output.split()))
        vocab_ratio = unique_words / max(word_count, 1)
        scores["vocabulary_diversity"] = round(min(1.0, vocab_ratio * 2), 3)

        scores["structure"] = round(min(1.0, output.count(".") / 5), 3)

        quality_penalty = 0.0
        issues_penalty = 0.0
        if reflection:
            quality_map = {"poor": 0.4, "low": 0.3, "medium": 0.1, "high": 0.0, "excellent": 0.0}
            quality_penalty = quality_map.get(reflection.get("quality", ""), 0.1)
            issues_penalty = len(reflection.get("issues", [])) * 0.08
            if reflection.get("contradictions"):
                issues_penalty += len(reflection["contradictions"]) * 0.15

        scores["quality_penalty"] = round(quality_penalty, 3)
        scores["issues_penalty"] = round(min(issues_penalty, 0.8), 3)

        signal_scores = [v for k, v in scores.items() if not k.endswith("penalty")]
        base = sum(signal_scores) / max(len(signal_scores), 1)
        total_penalty = min(quality_penalty + issues_penalty, 0.9)
        overall = max(0.05, min(1.0, base - total_penalty))

        if overall >= 0.8: level = "very_high"
        elif overall >= 0.6: level = "high"
        elif overall >= 0.4: level = "medium"
        elif overall >= 0.2: level = "low"
        else: level = "very_low"

        result = {
            "score": round(overall, 4),
            "level": level,
            "components": scores,
            "should_retry": overall < 0.25,
            "retry_reason": "Very low confidence" if overall < 0.25 else None,
        }
        self._calibration_data.append(result)
        return result

    def get_calibration(self) -> dict:
        if not self._calibration_data:
            return {"average": 0.0, "samples": 0, "calibration_error": 0.0}
        scores = [c["score"] for c in self._calibration_data]
        avg = sum(scores) / len(scores)
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)
        return {
            "average": round(avg, 4),
            "std_dev": round(math.sqrt(variance), 4),
            "samples": len(self._calibration_data),
            "calibration_error": round(variance, 4),
        }
