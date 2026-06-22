import difflib
import re
from typing import Any, Dict, List, Optional


class Evaluator:
    def __init__(self):
        self._weights = {
            "correctness": 0.40,
            "coherence": 0.25,
            "completeness": 0.20,
            "efficiency": 0.15,
        }
        self._evaluation_history: List[Dict] = []

    def score(self, task: Dict, output: Any, expected: Optional[Any] = None) -> Dict:
        correctness = 0.0
        if expected is not None:
            correctness = self.score_correctness(output, expected)

        chain = task.get("chain", task.get("reasoning_chain", []))
        coherence = self.score_coherence(chain)

        requirements = task.get("requirements", task.get("criteria", []))
        completeness = self.score_completeness(output, requirements)

        steps = task.get("steps_taken", task.get("steps", 1))
        optimal_steps = task.get("optimal_steps", steps)
        efficiency = self.score_efficiency(steps, optimal_steps)

        overall = (
            self._weights["correctness"] * correctness
            + self._weights["coherence"] * coherence
            + self._weights["completeness"] * completeness
            + self._weights["efficiency"] * efficiency
        )

        result = {
            "overall": round(overall, 4),
            "correctness": round(correctness, 4),
            "coherence": round(coherence, 4),
            "completeness": round(completeness, 4),
            "efficiency": round(efficiency, 4),
            "weights": self._weights,
        }
        self._evaluation_history.append({"task": task, "result": result})
        return result

    def score_correctness(self, output: Any, expected: Any) -> float:
        if output is None or expected is None:
            return 0.0

        if isinstance(output, (int, float)) and isinstance(expected, (int, float)):
            if expected == 0:
                return 1.0 if output == 0 else 0.0
            ratio = abs(output - expected) / max(abs(expected), 1e-10)
            return max(0.0, 1.0 - min(ratio, 1.0))

        if isinstance(output, bool) and isinstance(expected, bool):
            return 1.0 if output == expected else 0.0

        if isinstance(output, str) and isinstance(expected, str):
            seq = difflib.SequenceMatcher(None, output.lower(), expected.lower())
            return seq.ratio()

        if isinstance(output, (list, tuple)) and isinstance(expected, (list, tuple)):
            if len(output) == 0 and len(expected) == 0:
                return 1.0
            if len(output) == 0 or len(expected) == 0:
                return 0.0
            matches = sum(1 for a, b in zip(output, expected) if a == b)
            return matches / max(len(output), len(expected))

        if isinstance(output, dict) and isinstance(expected, dict):
            shared = set(output.keys()) & set(expected.keys())
            if not shared:
                return 0.0
            correct = sum(1 for k in shared if output[k] == expected[k])
            return correct / len(shared)

        return 1.0 if str(output) == str(expected) else 0.0

    def score_coherence(self, chain: List[str]) -> float:
        if not chain:
            return 0.0
        if len(chain) == 1:
            return 1.0

        contradiction_pairs = [
            (r"\bnot\s+\w+", r"\b(?:is|are|was|were)\s+\w+"),
            (r"\balways\b", r"\bnever\b"),
            (r"\ball\b", r"\bnone\b"),
            (r"\bincrease\b", r"\bdecrease\b"),
            (r"\bpositive\b", r"\bnegative\b"),
            (r"\btrue\b", r"\bfalse\b"),
            (r"\byes\b", r"\bno\b"),
            (r"\binclude\b", r"\bexclude\b"),
            (r"\bsupport\b", r"\boppose\b"),
            (r"\benable\b", r"\bdisable\b"),
        ]

        contradictions = 0
        total_pairs = 0

        for i in range(len(chain) - 1):
            for j in range(i + 1, min(len(chain), i + 4)):
                step_a = chain[i].lower()
                step_b = chain[j].lower()
                for pat_a, pat_b in contradiction_pairs:
                    has_a = bool(re.search(pat_a, step_a))
                    has_b = bool(re.search(pat_b, step_b))
                    if has_a and has_b:
                        contradictions += 1
                    total_pairs += 1

        if total_pairs == 0:
            return 0.8

        overlap_score = 0.0
        for i in range(len(chain) - 1):
            words_a = set(re.findall(r'\w+', chain[i].lower()))
            words_b = set(re.findall(r'\w+', chain[i + 1].lower()))
            if len(words_a) > 0 and len(words_b) > 0:
                jaccard = len(words_a & words_b) / len(words_a | words_b)
                overlap_score += jaccard
        avg_overlap = overlap_score / max(1, len(chain) - 1)
        logical_flow = min(1.0, avg_overlap * 3.0)

        contradiction_penalty = contradictions / max(1, total_pairs)
        coherence = max(0.0, (logical_flow * 0.7 + (1.0 - contradiction_penalty) * 0.3))
        return min(1.0, coherence)

    def score_completeness(self, output: Any, requirements: List[str]) -> float:
        if not requirements:
            return 1.0
        if output is None:
            return 0.0

        output_str = str(output).lower()
        if not output_str:
            return 0.0

        matched = 0
        for req in requirements:
            req_lower = req.lower()
            keywords = re.findall(r'\w+', req_lower)
            if not keywords:
                continue
            if len(keywords) == 1:
                if keywords[0] in output_str:
                    matched += 1
            else:
                found = sum(1 for kw in keywords if kw in output_str)
                if found / len(keywords) >= 0.5:
                    matched += 1

        return matched / len(requirements)

    def score_efficiency(self, steps: int, optimal_steps: int) -> float:
        if steps <= 0:
            return 0.0
        if optimal_steps <= 0:
            optimal_steps = 1
        ratio = optimal_steps / max(steps, 1)
        return min(1.0, ratio)

    def evaluate(self, task: Dict, output: Any, expected: Optional[Any] = None) -> Dict:
        return self.score(task, output, expected)
