"""NICTO X — Self-reflection with deep critique, contradiction detection, and quality assessment."""

from __future__ import annotations

import logging
import re
import time
from typing import Optional

logger = logging.getLogger("nicto_x.reasoning.reflection")


class SelfReflection:
    """Deep self-evaluation: critiques outputs, detects contradictions, assesses quality, suggests improvements."""

    QUALITY_METRICS = ["clarity", "accuracy", "depth", "relevance", "coherence", "completeness"]

    def __init__(self):
        self._reflection_history: list[dict] = []

    def evaluate(self, input_text: str, output: str) -> dict:
        issues = []
        suggestions = []

        input_words = len(input_text.split())
        output_words = len(output.split())

        if output_words < max(3, input_words * 0.2):
            issues.append("output_too_short")
            suggestions.append("Expand with more detailed analysis")
        elif output_words < max(3, input_words * 0.5):
            issues.append("output_somewhat_short")
            suggestions.append("Consider adding supporting evidence")

        if output.strip() == input_text.strip():
            issues.append("merely_repeated_input")
            suggestions.append("Generate novel analysis rather than repeating input")

        unique_words = set(w.lower() for w in output.split())
        if len(unique_words) < 5:
            issues.append("low_vocabulary_diversity")
            suggestions.append("Use a broader range of terminology")

        contradictions = self._detect_contradictions(output)
        if contradictions:
            issues.append("contains_contradictions")
            suggestions.append("Resolve contradictory statements")
        else:
            suggestions.append("Output appears internally consistent")

        hedging = self._detect_hedging(output)
        if hedging:
            issues.append("excessive_hedging")
            suggestions.append("Use more definitive language where confident")
            for h in hedging:
                suggestions.append(f"Avoid overuse of '{h}'")

        reasoning_gaps = self._find_reasoning_gaps(output)
        if reasoning_gaps:
            issues.append("reasoning_gaps")
            suggestions.extend(reasoning_gaps)

        metrics = self._score_quality(input_text, output, issues, contradictions)
        quality = self._classify_quality(metrics["overall"])

        result = {
            "issues": issues,
            "quality": quality,
            "scores": metrics,
            "contradictions": contradictions,
            "hedging_phrases": hedging,
            "suggestions": suggestions[:5],
            "word_count": output_words,
            "unique_word_ratio": round(len(unique_words) / max(output_words, 1), 3),
            "timestamp": time.time(),
        }
        self._reflection_history.append(result)
        return result

    def _detect_contradictions(self, text: str) -> list[str]:
        text_lower = text.lower()
        contradiction_pairs = [
            ("always", "never"), ("increase", "decrease"), ("positive", "negative"),
            ("all", "none"), ("must", "must not"), ("everyone", "no one"),
            ("always", "sometimes not"), ("definitely", "possibly not"),
            ("certain", "uncertain"), ("proven", "disproven"),
            ("support", "contradict"), ("confirm", "deny"),
        ]
        found = []
        for a, b in contradiction_pairs:
            if a in text_lower and b in text_lower:
                found.append(f"'{a}' vs '{b}'")
        return found

    def _detect_hedging(self, text: str) -> list[str]:
        phrases = ["i think", "maybe", "perhaps", "might be", "could be", "possibly",
                    "it seems", "i believe", "in my opinion", "sort of", "kind of",
                    "generally speaking", "to some extent", "it appears"]
        found = [p for p in phrases if p in text.lower()]
        return found

    def _find_reasoning_gaps(self, text: str) -> list[str]:
        gaps = []
        claim_patterns = [
            (r"because", "Claim without evidence"),
            (r"therefore", "Conclusion without clear premises"),
            (r"implies?", "Unsupported implication"),
            (r"clearly", "Assertion without justification"),
        ]
        for pattern, gap_desc in claim_patterns:
            if re.search(pattern, text.lower()):
                pass
        if len(text.split(".")) < 3:
            gaps.append("Break analysis into multiple structured sentences")
        return gaps

    def _score_quality(self, input_text: str, output: str, issues: list, contradictions: list) -> dict:
        clarity = min(1.0, len(output.split()) / 100)
        depth = min(1.0, len(set(output.split())) / 30)
        relevance = 0.8 if len(set(input_text.lower().split()) & set(output.lower().split())) > 3 else 0.4
        coherence = max(0.3, 1.0 - len(contradictions) * 0.2)
        completeness = min(1.0, len(output) / 500)
        accuracy = max(0.3, 1.0 - len(issues) * 0.1)

        overall = (clarity + depth + relevance + coherence + completeness + accuracy) / 6
        return {
            "clarity": round(clarity, 3),
            "depth": round(depth, 3),
            "relevance": round(relevance, 3),
            "coherence": round(coherence, 3),
            "completeness": round(completeness, 3),
            "accuracy": round(accuracy, 3),
            "overall": round(overall, 3),
        }

    def _classify_quality(self, score: float) -> str:
        if score >= 0.8: return "excellent"
        if score >= 0.6: return "high"
        if score >= 0.4: return "medium"
        if score >= 0.2: return "low"
        return "poor"

    def get_history(self, limit: int = 10) -> list[dict]:
        return self._reflection_history[-limit:]
