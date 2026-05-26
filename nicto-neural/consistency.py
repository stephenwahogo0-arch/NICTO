from typing import Any, Callable, Dict, List
import difflib


class ConsistencyTracker:
    def __init__(self):
        self.history: Dict[str, List[str]] = {}

    def logical_coherence(self, chain: List[str]) -> float:
        if len(chain) < 2:
            return 1.0
        coherence = 0.0
        for i in range(len(chain) - 1):
            seq = difflib.SequenceMatcher(None, chain[i].lower(), chain[i + 1].lower())
            coherence += seq.ratio()
        return coherence / (len(chain) - 1)

    def output_stability(self, task: Dict, func: Callable, n_runs: int = 5) -> float:
        outputs = []
        for _ in range(n_runs):
            try:
                out = func(task)
                outputs.append(str(out))
            except Exception:
                outputs.append("")
        if len(outputs) < 2:
            return 1.0
        if len(set(outputs)) == 1:
            return 1.0
        scores = []
        for i in range(len(outputs)):
            for j in range(i + 1, len(outputs)):
                seq = difflib.SequenceMatcher(None, outputs[i], outputs[j])
                scores.append(seq.ratio())
        return sum(scores) / len(scores) if scores else 0.0

    def record_output(self, task_id: str, output: str) -> None:
        if task_id not in self.history:
            self.history[task_id] = []
        self.history[task_id].append(output)

    def get_stability(self, task_id: str) -> float:
        outputs = self.history.get(task_id, [])
        if len(outputs) < 2:
            return 1.0
        scores = []
        for i in range(len(outputs)):
            for j in range(i + 1, len(outputs)):
                seq = difflib.SequenceMatcher(None, outputs[i], outputs[j])
                scores.append(seq.ratio())
        return sum(scores) / len(scores) if scores else 0.0
