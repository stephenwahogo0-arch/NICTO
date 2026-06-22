from typing import Any, Dict, List, Optional
import time


class ReflectionEngine:
    def __init__(self):
        self.history: List[Dict] = []

    def reflect(self, task: Dict, result: Dict) -> Dict:
        score = result.get("total", 0.0) or result.get("accuracy", 0.0)
        was_successful = score >= 0.7
        reflection = {
            "timestamp": time.time(),
            "task_input": task.get("input", str(task)),
            "task_domain": task.get("domain", "general"),
            "expected": task.get("expected"),
            "actual": result.get("output", result.get("actual")),
            "score": score,
            "was_successful": was_successful,
            "error_type": None,
            "improvement_suggestion": None,
            "difficulty": task.get("difficulty", 0),
        }
        if not was_successful:
            reflection["error_type"] = self._classify_error(task, result)
            reflection["improvement_suggestion"] = self._suggest_improvement(task, result)
        self.history.append(reflection)
        return reflection

    def _classify_error(self, task: Dict, result: Dict) -> str:
        output = str(result.get("output", result.get("actual", "")))
        expected = str(task.get("expected", ""))
        if not output and expected:
            return "empty_output"
        if len(output) > 0 and len(expected) > 0 and len(output) < len(expected) * 0.3:
            return "too_short"
        if len(output) > len(expected) * 3:
            return "too_long"
        common = sum(1 for a, b in zip(output, expected) if a == b)
        if common > 0 and common < min(len(output), len(expected)) * 0.5:
            return "partially_correct"
        return "incorrect"

    def _suggest_improvement(self, task: Dict, result: Dict) -> str:
        error = self._classify_error(task, result)
        suggestions = {
            "empty_output": "Ensure the model generates a non-empty response for this input domain",
            "too_short": "Train for more detailed and comprehensive responses",
            "too_long": "Train for more concise and focused responses",
            "partially_correct": "Focus on the specific patterns where partial matches occur",
            "incorrect": "Re-train with more examples covering this input space",
        }
        return suggestions.get(error, "Review training data for this domain")

    def get_recent(self, n: int = 10) -> List[Dict]:
        return self.history[-n:]

    def get_mistakes(self, min_score: float = 0.0, max_score: float = 0.7) -> List[Dict]:
        return [r for r in self.history if min_score <= r["score"] < max_score]
