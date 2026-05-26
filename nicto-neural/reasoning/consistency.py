"""Consistency tracker — logical coherence + output stability."""


class ConsistencyTracker:
    """σ = 0.6 * logical_coherence + 0.4 * output_stability."""

    def __init__(self):
        self._chains: dict[str, list] = {}
        self._output_cache: dict[str, list] = {}
        self._contradiction_count = 0
        self._total_steps = 0

    def logical_coherence(self, chain: list[str]) -> float:
        """Check for contradictions between consecutive steps."""
        if len(chain) < 2:
            return 1.0

        contradictions = 0
        for i in range(len(chain) - 1):
            if self._contradicts(chain[i], chain[i + 1]):
                contradictions += 1

        self._contradiction_count += contradictions
        self._total_steps += len(chain)

        score = 1.0 - (contradictions / len(chain))
        return max(0.0, score)

    def output_stability(self, task: str, output: str, n_history: int = 5) -> float:
        """Measure variance in outputs for the same task."""
        if task not in self._output_cache:
            self._output_cache[task] = []
        self._output_cache[task].append(output)

        history = self._output_cache[task][-n_history:]
        if len(history) < 2:
            return 1.0

        lengths = [len(o) for o in history]
        mean_len = sum(lengths) / len(lengths)
        variance = sum((ln - mean_len) ** 2 for ln in lengths) / len(lengths)
        normalized_var = min(1.0, variance / (mean_len ** 2 + 1e-8))

        return 1.0 - normalized_var

    def sigma(self, chain: list[str], task: str, output: str) -> float:
        """Combined consistency metric σ."""
        coherence = self.logical_coherence(chain)
        stability = self.output_stability(task, output)
        return 0.6 * coherence + 0.4 * stability

    def _contradicts(self, step_a: str, step_b: str) -> bool:
        """Simple contradiction detection."""
        a, b = step_a.lower(), step_b.lower()
        contradiction_pairs = [
            ("true", "false"),
            ("yes", "no"),
            ("correct", "incorrect"),
            ("valid", "invalid"),
            ("always", "never"),
            ("is", "is not"),
        ]
        for pos, neg in contradiction_pairs:
            if pos in a and neg in b:
                return True
            if neg in a and pos in b:
                return True
        return False

    def get_stats(self) -> dict:
        return {
            "total_steps_tracked": self._total_steps,
            "total_contradictions": self._contradiction_count,
            "global_coherence": 1.0 - (
                self._contradiction_count / max(self._total_steps, 1)
            ),
            "tasks_tracked": len(self._output_cache),
        }
