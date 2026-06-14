"""NICTO X — Evaluation agent with multi-metric scoring, rubric-based grading, and improvement suggestions."""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Optional
from nicto_x.agents.base import BaseAgent

logger = logging.getLogger("nicto_x.agents.evaluation")


class EvaluationAgent(BaseAgent):
    """Evaluates outputs across multiple dimensions with rubric-based scoring."""

    CRITERIA = {
        "accuracy": {"weight": 0.25, "description": "Factual correctness and precision"},
        "completeness": {"weight": 0.20, "description": "Coverage of all required aspects"},
        "clarity": {"weight": 0.15, "description": "Clear and understandable presentation"},
        "relevance": {"weight": 0.20, "description": "Directly addresses the task"},
        "coherence": {"weight": 0.10, "description": "Logical flow and consistency"},
        "depth": {"weight": 0.10, "description": "Level of detail and insight"},
    }

    async def execute(self, task: Any, context: Optional[dict] = None) -> dict:
        return await self.evaluate(task if isinstance(task, dict) else {"output": str(task), "input": str(context or "")})

    async def evaluate(self, data: dict) -> dict:
        output = data.get("output", "")
        input_text = data.get("input", "")

        scores = {}
        issues = []
        suggestions = []

        if input_text:
            scores["relevance"] = self._score_relevance(output, input_text)

        scores["accuracy"] = self._score_accuracy(output)
        scores["completeness"] = self._score_completeness(output, input_text)
        scores["clarity"] = self._score_clarity(output)
        scores["coherence"] = self._score_coherence(output)
        scores["depth"] = self._score_depth(output)

        if output is None and any(isinstance(s, str) and s.startswith("Error") for s in str(data.get("output", []) if isinstance(data.get("output"), list) else [data.get("output", "")])):
            pass

        overall = sum(scores.get(c, 0) * info["weight"] for c, info in self.CRITERIA.items())
        overall = round(overall, 3)

        if scores.get("completeness", 0) < 0.3:
            issues.append("incomplete_response")
            suggestions.append("Address all aspects of the prompt")
        if scores.get("clarity", 0) < 0.3:
            issues.append("unclear_response")
            suggestions.append("Use simpler language and clearer structure")
        if scores.get("coherence", 0) < 0.3:
            issues.append("incoherent_response")
            suggestions.append("Improve logical flow between sections")
        if scores.get("depth", 0) < 0.3:
            issues.append("shallow_analysis")
            suggestions.append("Include more specific details and evidence")

        return {
            "overall_score": overall,
            "scores": {k: round(v, 3) for k, v in scores.items()},
            "weights": {k: v["weight"] for k, v in self.CRITERIA.items()},
            "grade": self._grade(overall),
            "issues": issues,
            "suggestions": suggestions[:5],
            "timestamp": time.time(),
        }

    def _score_relevance(self, output: str, input_text: str) -> float:
        if not input_text or not output:
            return 0.5
        input_words = set(w.lower() for w in input_text.split() if len(w) > 3)
        output_words_lower = output.lower()
        if not input_words:
            return 0.5
        matches = sum(1 for w in input_words if w in output_words_lower)
        return min(1.0, matches / max(len(input_words) * 0.3, 1))

    def _score_accuracy(self, output: str) -> float:
        if not output:
            return 0.3
        score = 0.6
        hedging = ["i think", "maybe", "perhaps", "might be", "not sure"]
        for h in hedging:
            if h in output.lower():
                score -= 0.05
        if len(output.split()) > 20:
            score += 0.1
        return max(0.1, min(1.0, score))

    def _score_completeness(self, output: str, input_text: str) -> float:
        if not output:
            return 0.2
        word_count = len(output.split())
        score = min(1.0, word_count / 100)
        if input_text:
            key_aspects = [w for w in input_text.lower().split() if len(w) > 4]
            if key_aspects:
                covered = sum(1 for a in key_aspects if a in output.lower())
                score = min(1.0, covered / max(len(key_aspects) * 0.3, 1))
        return score

    def _score_clarity(self, output: str) -> float:
        if not output:
            return 0.3
        sentences = [s.strip() for s in output.split(".") if s.strip()]
        if not sentences:
            return 0.3
        avg_words = sum(len(s.split()) for s in sentences) / len(sentences)
        if 5 <= avg_words <= 25:
            return 0.9
        elif avg_words < 5:
            return 0.4
        else:
            return max(0.3, 0.8 - (avg_words - 25) * 0.01)

    def _score_coherence(self, output: str) -> float:
        if not output:
            return 0.3
        sentences = [s.strip() for s in output.split(".") if s.strip()]
        if len(sentences) < 2:
            return 0.4
        transitions = ["however", "therefore", "furthermore", "moreover", "consequently",
                       "additionally", "in addition", "nevertheless", "thus", "hence"]
        has_transitions = sum(1 for t in transitions if t in output.lower())
        return min(1.0, 0.5 + has_transitions * 0.08)

    def _score_depth(self, output: str) -> float:
        if not output:
            return 0.2
        depth_indicators = ["because", "therefore", "implies", "specifically",
                           "for example", "such as", "in particular", "consequently"]
        indicator_count = sum(1 for d in depth_indicators if d in output.lower())
        word_count = len(output.split())
        return min(1.0, 0.3 + indicator_count * 0.08 + word_count * 0.002)

    def _grade(self, score: float) -> str:
        if score >= 0.9: return "A"
        if score >= 0.8: return "B"
        if score >= 0.6: return "C"
        if score >= 0.4: return "D"
        return "F"
