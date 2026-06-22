import json
import os
import time
from typing import Any, Dict, List, Optional
from collections import defaultdict


class MemoryManager:
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(os.path.expanduser("~"), ".nikto", "memory")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.episodic: List[Dict] = []
        self.semantic: Dict[str, Any] = {}
        self.skills: Dict[str, Any] = {}
        self.goals: List[Dict] = []
        self.reflections: List[Dict] = []
        self.performance: List[Dict] = []
        self.task_features: List[Dict] = []
        self.consistency: List[Dict] = []
        self.experience: List[Dict] = []
        self._load_all()

    def _load_all(self):
        mapping = {
            "episodic.json": "episodic",
            "semantic.json": "semantic",
            "skills.json": "skills",
            "goals.json": "goals",
            "reflections.json": "reflections",
            "performance.json": "performance",
            "task_features.json": "task_features",
            "consistency.json": "consistency",
            "experience.json": "experience",
        }
        for fname, attr in mapping.items():
            path = os.path.join(self.storage_dir, fname)
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        setattr(self, attr, json.load(f))
                except Exception:
                    pass

    def _save_all(self):
        mapping = {
            "episodic.json": "episodic",
            "semantic.json": "semantic",
            "skills.json": "skills",
            "goals.json": "goals",
            "reflections.json": "reflections",
            "performance.json": "performance",
            "task_features.json": "task_features",
            "consistency.json": "consistency",
            "experience.json": "experience",
        }
        for fname, attr in mapping.items():
            path = os.path.join(self.storage_dir, fname)
            try:
                with open(path, "w") as f:
                    json.dump(getattr(self, attr), f, indent=2)
            except Exception:
                pass

    def store_episodic(self, item: Dict) -> None:
        item["_timestamp"] = time.time()
        self.episodic.append(item)
        self._save_all()

    def store_semantic(self, key: str, value: Any) -> None:
        self.semantic[key] = {"value": value, "_timestamp": time.time()}
        self._save_all()

    def store_skill(self, name: str, data: Any) -> None:
        self.skills[name] = {"data": data, "_timestamp": time.time()}
        self._save_all()

    def store_goal(self, goal: Dict) -> None:
        goal["_timestamp"] = time.time()
        self.goals.append(goal)
        self._save_all()

    def store_reflection(self, reflection: Dict) -> None:
        reflection["_timestamp"] = time.time()
        self.reflections.append(reflection)
        self._save_all()

    def store_performance(self, perf: Dict) -> None:
        perf["_timestamp"] = time.time()
        self.performance.append(perf)
        self._save_all()

    def store_task_feature(self, feature: Dict) -> None:
        feature["_timestamp"] = time.time()
        self.task_features.append(feature)
        self._save_all()

    def store_consistency(self, entry: Dict) -> None:
        entry["_timestamp"] = time.time()
        self.consistency.append(entry)
        self._save_all()

    def store_experience(self, exp: Dict) -> None:
        exp["_timestamp"] = time.time()
        self.experience.append(exp)
        self._save_all()

    def get_conversations(self, limit: int = 1000) -> List[Dict]:
        return [e for e in self.episodic if e.get("type") == "conversation"][-limit:]

    def get_task_history(self, limit: int = 1000) -> List[Dict]:
        return [e for e in self.episodic if e.get("type") == "task"][-limit:]

    def get_reflections(self, limit: int = 1000) -> List[Dict]:
        return self.reflections[-limit:]

    def get_tool_outputs(self, limit: int = 1000) -> List[Dict]:
        return [e for e in self.episodic if e.get("type") == "tool"][-limit:]

    def get_user_corrections(self, limit: int = 1000) -> List[Dict]:
        return [e for e in self.episodic if e.get("type") == "correction"][-limit:]

    def get_accuracy_history(self, brain: str, domain: str) -> List[float]:
        return [
            p["accuracy"] for p in self.performance
            if p.get("brain") == brain and p.get("domain") == domain and "accuracy" in p
        ]

    def get_performance_history(self, metric: str = None) -> List[Dict]:
        if metric:
            return [p for p in self.performance if p.get("metric") == metric]
        return self.performance

    def clear(self) -> None:
        self.episodic.clear()
        self.semantic.clear()
        self.skills.clear()
        self.goals.clear()
        self.reflections.clear()
        self.performance.clear()
        self.task_features.clear()
        self.consistency.clear()
        self.experience.clear()
        self._save_all()
