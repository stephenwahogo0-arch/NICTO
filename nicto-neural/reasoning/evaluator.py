"""Output evaluator — quality scoring for brain outputs."""


class OutputEvaluator:
    """Scores output quality across multiple dimensions."""

    def __init__(self):
        self._history: list[dict] = []

    def evaluate(
        self,
        task: str,
        output: str,
        confidence: float,
        domain: str = "general",
    ) -> dict:
        """Score output quality on 0-1 scale across dimensions."""
        relevance = self._score_relevance(task, output)
        completeness = self._score_completeness(output)
        coherence = self._score_coherence(output)
        specificity = self._score_specificity(output)

        overall = (
            0.3 * relevance
            + 0.25 * completeness
            + 0.25 * coherence
            + 0.2 * specificity
        )

        result = {
            "overall": overall,
            "relevance": relevance,
            "completeness": completeness,
            "coherence": coherence,
            "specificity": specificity,
            "confidence": confidence,
            "domain": domain,
        }
        self._history.append(result)
        return result

    def _score_relevance(self, task: str, output: str) -> float:
        task_words = set(task.lower().split())
        output_words = set(output.lower().split())
        if not task_words:
            return 0.5
        overlap = len(task_words & output_words)
        return min(1.0, overlap / max(len(task_words) * 0.3, 1))

    def _score_completeness(self, output: str) -> float:
        word_count = len(output.split())
        if word_count < 5:
            return 0.2
        if word_count < 20:
            return 0.5
        if word_count < 100:
            return 0.8
        return 1.0

    def _score_coherence(self, output: str) -> float:
        sentences = output.split(".")
        if len(sentences) < 2:
            return 0.7
        return min(1.0, 0.6 + len(sentences) * 0.05)

    def _score_specificity(self, output: str) -> float:
        specific_indicators = [
            "specifically", "for example", "such as", "because",
            "therefore", "however", "in particular",
        ]
        count = sum(1 for ind in specific_indicators if ind in output.lower())
        return min(1.0, 0.3 + count * 0.15)

    def average_quality(self, n_recent: int = 20) -> float:
        if not self._history:
            return 0.0
        recent = self._history[-n_recent:]
        return sum(r["overall"] for r in recent) / len(recent)

    def trend(self) -> str:
        if len(self._history) < 5:
            return "insufficient_data"
        recent = [r["overall"] for r in self._history[-5:]]
        if recent[-1] > recent[0] + 0.05:
            return "improving"
        if recent[-1] < recent[0] - 0.05:
            return "degrading"
        return "stable"
