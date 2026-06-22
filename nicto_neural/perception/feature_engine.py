import numpy as np
import time
from typing import Dict, List, Any


class FeatureEngine:
    def __init__(self):
        self._feature_names = [
            "task_type",
            "domain",
            "complexity",
            "reasoning_depth",
            "confidence_trajectory",
            "memory_recall_count",
            "recency",
            "brain_activation_count",
            "time_elapsed_ms",
            "tool_call_frequency",
            "coherence_score",
            "exploration_rate",
            "curriculum_level",
            "reward_trajectory",
            "hacking_flag",
        ]

    def feature_names(self) -> List[str]:
        return list(self._feature_names)

    def extract(self, task: Dict[str, Any]) -> np.ndarray:
        features = np.zeros(15, dtype=np.float32)

        task_type = task.get("task_type", "analyze")
        type_map = {
            "code": 0.0, "question": 0.2, "creative": 0.4,
            "plan": 0.6, "retrieve": 0.8, "analyze": 1.0,
        }
        features[0] = type_map.get(task_type, 0.5)

        domain = task.get("domain", "")
        domain_hash = abs(hash(domain)) % 1000 / 1000.0 if domain else 0.5
        features[1] = domain_hash

        features[2] = np.clip(float(task.get("complexity", 0.5)), 0.0, 1.0)
        features[3] = np.clip(float(task.get("reasoning_depth", 0.3)), 0.0, 1.0)
        features[4] = np.clip(float(task.get("confidence_trajectory", 0.5)), 0.0, 1.0)
        features[5] = np.clip(float(task.get("memory_recall_count", 0)), 0.0, 100.0) / 100.0

        recency = task.get("recency", None)
        if recency is None:
            features[6] = 1.0
        elif isinstance(recency, (int, float)):
            features[6] = np.clip(1.0 / (1.0 + abs(float(recency))), 0.0, 1.0)
        else:
            features[6] = 0.5

        features[7] = np.clip(float(task.get("brain_activation_count", 1)), 0.0, 50.0) / 50.0

        time_ms = task.get("time_elapsed_ms", None)
        if time_ms is None and "timestamp" in task:
            time_ms = (time.time() - float(task["timestamp"])) * 1000
        features[8] = np.clip(float(time_ms if time_ms is not None else 0), 0.0, 10000.0) / 10000.0

        features[9] = np.clip(float(task.get("tool_call_frequency", 0)), 0.0, 100.0) / 100.0
        features[10] = np.clip(float(task.get("coherence_score", 0.7)), 0.0, 1.0)
        features[11] = np.clip(float(task.get("exploration_rate", 0.1)), 0.0, 1.0)
        features[12] = np.clip(float(task.get("curriculum_level", 0)), 0.0, 10.0) / 10.0
        features[13] = np.clip(float(task.get("reward_trajectory", 0.0)), -1.0, 1.0) * 0.5 + 0.5

        hacking_flag = task.get("hacking_flag", False)
        flags = task.get("flags", [])
        if isinstance(flags, list) and "hacking" in flags:
            hacking_flag = True
        features[14] = 1.0 if hacking_flag else 0.0

        return features
