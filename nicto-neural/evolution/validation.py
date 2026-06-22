import random
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import defaultdict


class ValidationEngine:
    def __init__(self, evaluator=None, elo_system=None):
        self.evaluator = evaluator
        self.elo = elo_system

    def split(self, dataset: List[Dict], val_ratio: float = 0.2) -> Tuple[List[Dict], List[Dict]]:
        shuffled = list(dataset)
        random.shuffle(shuffled)
        split_idx = int(len(shuffled) * (1 - val_ratio))
        train_set = shuffled[:split_idx]
        val_set = shuffled[split_idx:]
        return train_set, val_set

    def validate(self, model_func: Callable, val_set: List[Dict]) -> Dict:
        results = []
        for example in val_set:
            try:
                output = model_func(example)
            except Exception:
                output = ""
            expected = example.get("expected", "")
            if self.evaluator:
                score_result = self.evaluator.score(example, output, expected)
                score = score_result.get("total", 0.0)
            else:
                score = 1.0 if str(output) == str(expected) else 0.0
            results.append({
                "input": example.get("input", ""),
                "output": output,
                "expected": expected,
                "score": score,
                "domain": example.get("domain", "general"),
                "brain": example.get("brain_used", "default"),
            })
        return self.accuracy_report({"results": results, "total": len(results)})

    def accuracy_report(self, results: Dict) -> Dict:
        entries = results.get("results", [])
        if not entries:
            return {
                "accuracy": 0.0,
                "correct": 0,
                "total": 0,
                "per_domain": {},
                "per_brain": {},
                "confusion_matrix": {},
            }
        correct = sum(1 for r in entries if r.get("score", 0.0) >= 0.7)
        total = len(entries)
        accuracy = correct / total if total > 0 else 0.0
        return {
            "accuracy": accuracy,
            "correct": correct,
            "total": total,
            "per_domain": self.per_domain_accuracy(entries),
            "per_brain": self.per_brain_accuracy(entries),
            "confusion_matrix": self.confusion_matrix(entries),
        }

    def per_domain_accuracy(self, results: List[Dict]) -> Dict[str, float]:
        domain_scores: Dict[str, List[float]] = defaultdict(list)
        for r in results:
            domain_scores[r.get("domain", "general")].append(r.get("score", 0.0))
        return {d: sum(s) / len(s) for d, s in domain_scores.items()}

    def per_brain_accuracy(self, results: List[Dict]) -> Dict[str, float]:
        brain_scores: Dict[str, List[float]] = defaultdict(list)
        for r in results:
            brain_scores[r.get("brain", "default")].append(r.get("score", 0.0))
        return {b: sum(s) / len(s) for b, s in brain_scores.items()}

    def confusion_matrix(self, results: List[Dict]) -> Dict:
        matrix: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for r in results:
            expected = str(r.get("expected", ""))[:50]
            actual = str(r.get("output", ""))[:50]
            matrix[expected][actual] += 1
        return {k: dict(v) for k, v in matrix.items()}

    def hold_out_validate(self, model_func: Callable, held_out_set: List[Dict]) -> Dict:
        return self.validate(model_func, held_out_set)
