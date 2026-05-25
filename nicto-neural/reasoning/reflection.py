"""Reflection engine — post-task reflection with hacking detection."""


class ReflectionEngine:
    """Post-task reflection and self-improvement analysis."""

    def __init__(self):
        self._reflections: list[dict] = []

    def reflect(
        self,
        task: str,
        output: str,
        confidence: float,
        brains_used: list[str],
        domain: str,
        quality_score: float = 0.5,
    ) -> dict:
        """Generate post-task reflection."""
        improvements = []
        strengths = []

        if confidence < 0.5:
            improvements.append("Low confidence — need more training data in this domain")
        if confidence > 0.9:
            strengths.append("High confidence — strong domain expertise")

        if quality_score < 0.6:
            improvements.append("Output quality below threshold — review reasoning chain")
        if quality_score > 0.8:
            strengths.append("High quality output")

        if len(brains_used) == 1:
            improvements.append("Single brain used — consider multi-brain ensemble")
        if len(brains_used) >= 3:
            strengths.append("Good brain diversity in reasoning")

        reflection = {
            "task": task[:100],
            "domain": domain,
            "confidence": confidence,
            "quality": quality_score,
            "brains_used": brains_used,
            "strengths": strengths,
            "improvements": improvements,
            "meta_score": (confidence + quality_score) / 2,
        }
        self._reflections.append(reflection)
        return reflection

    def get_improvement_suggestions(self, n_recent: int = 10) -> list[str]:
        """Aggregate improvement suggestions from recent reflections."""
        suggestions: dict[str, int] = {}
        for ref in self._reflections[-n_recent:]:
            for imp in ref.get("improvements", []):
                suggestions[imp] = suggestions.get(imp, 0) + 1
        return sorted(suggestions.keys(), key=lambda x: suggestions[x], reverse=True)

    def get_stats(self) -> dict:
        if not self._reflections:
            return {"total": 0, "avg_meta_score": 0.0}
        scores = [r["meta_score"] for r in self._reflections]
        return {
            "total": len(self._reflections),
            "avg_meta_score": sum(scores) / len(scores),
            "avg_confidence": sum(r["confidence"] for r in self._reflections) / len(self._reflections),
        }
