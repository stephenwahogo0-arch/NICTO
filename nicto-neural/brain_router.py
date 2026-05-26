from typing import Any, Dict, List, Optional
import numpy as np


class BrainRouter:
    def __init__(self, elo_estimator=None):
        self.elo = elo_estimator
        self.domain_map: Dict[str, List[str]] = {}

    def register_brain(self, brain: str, domains: List[str]) -> None:
        for d in domains:
            if d not in self.domain_map:
                self.domain_map[d] = []
            if brain not in self.domain_map[d]:
                self.domain_map[d].append(brain)

    def best_brain_for(self, task: Dict) -> Optional[str]:
        domain = task.get("domain", "general")
        candidates = self.domain_map.get(domain, [])
        if not candidates:
            return None
        if self.elo is None:
            return candidates[0]
        best = None
        best_rating = -1
        for brain in candidates:
            r = self.elo.get_rating(brain, domain)
            if r > best_rating:
                best_rating = r
                best = brain
        return best

    def merge(self, outputs: List[Any], confidences: List[float]) -> Any:
        if not outputs:
            return None
        if len(outputs) == 1:
            return outputs[0]
        total_conf = sum(confidences)
        if total_conf == 0:
            return outputs[0]
        weights = [c / total_conf for c in confidences]
        if all(isinstance(o, (int, float)) for o in outputs):
            return sum(w * o for w, o in zip(weights, outputs))
        if all(isinstance(o, str) for o in outputs):
            return max(zip(outputs, confidences), key=lambda x: x[1])[0]
        if all(isinstance(o, list) for o in outputs):
            return max(zip(outputs, confidences), key=lambda x: x[1])[0]
        if all(isinstance(o, dict) for o in outputs):
            merged = {}
            for o, w in zip(outputs, confidences):
                for k, v in o.items():
                    if k not in merged:
                        merged[k] = (v, w)
                    else:
                        existing_val, existing_w = merged[k]
                        if isinstance(v, (int, float)) and isinstance(existing_val, (int, float)):
                            merged[k] = (existing_val * existing_w + v * w) / (existing_w + w)
                        else:
                            merged[k] = v if w > existing_w else existing_val
            return {k: v[0] if isinstance(v, tuple) else v for k, v in merged.items()}
        return outputs[np.argmax(confidences)]
