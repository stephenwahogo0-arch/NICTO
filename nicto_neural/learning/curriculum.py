import random
import math
from typing import Dict, List, Optional


class Curriculum:
    def __init__(self):
        self.levels: Dict[str, Dict[str, int]] = {}
        self.max_level = 5
        self.plateau_window = 5
        self.unlock_threshold = 0.75

    def get_level(self, brain: str, domain: str) -> int:
        return self.levels.get(brain, {}).get(domain, 0)

    def set_level(self, brain: str, domain: str, level: int) -> None:
        if brain not in self.levels:
            self.levels[brain] = {}
        self.levels[brain][domain] = max(0, min(self.max_level, level))

    def should_unlock(self, brain: str, domain: str, accuracy_history: List[float]) -> bool:
        current = self.get_level(brain, domain)
        if current >= self.max_level:
            return False
        if self.plateau_detected(accuracy_history):
            recent = accuracy_history[-self.plateau_window:]
            if all(a >= self.unlock_threshold for a in recent):
                return True
        return False

    def unlock_next(self, brain: str, domain: str) -> int:
        current = self.get_level(brain, domain)
        if current < self.max_level:
            new_level = current + 1
            self.set_level(brain, domain, new_level)
            return new_level
        return current

    def max_possible_level(self, brain: str, domain: str) -> int:
        return self.max_level

    def tasks_for_level(self, level: int, brain: str, domain: str) -> List[Dict]:
        templates = {
            0: [
                {"input": f"Basic {domain} task A", "expected": "Simple answer 1", "domain": domain, "difficulty": 0},
                {"input": f"Basic {domain} task B", "expected": "Simple answer 2", "domain": domain, "difficulty": 0},
            ],
            1: [
                {"input": f"Easy {domain} task A", "expected": "Straightforward answer 1", "domain": domain, "difficulty": 1},
                {"input": f"Easy {domain} task B", "expected": "Straightforward answer 2", "domain": domain, "difficulty": 1},
            ],
            2: [
                {"input": f"Medium {domain} task A", "expected": "Moderate answer 1", "domain": domain, "difficulty": 2},
                {"input": f"Medium {domain} task B", "expected": "Moderate answer 2", "domain": domain, "difficulty": 2},
            ],
            3: [
                {"input": f"Hard {domain} task A", "expected": "Complex answer 1", "domain": domain, "difficulty": 3},
                {"input": f"Hard {domain} task B", "expected": "Complex answer 2", "domain": domain, "difficulty": 3},
            ],
            4: [
                {"input": f"Expert {domain} task A", "expected": "Advanced answer 1", "domain": domain, "difficulty": 4},
                {"input": f"Expert {domain} task B", "expected": "Advanced answer 2", "domain": domain, "difficulty": 4},
            ],
            5: [
                {"input": f"Master {domain} task A", "expected": "Expert answer 1", "domain": domain, "difficulty": 5},
                {"input": f"Master {domain} task B", "expected": "Expert answer 2", "domain": domain, "difficulty": 5},
            ],
        }
        level = max(0, min(self.max_level, level))
        tasks = templates.get(level, templates[0])
        return [dict(t, brain_used=brain) for t in tasks]

    def plateau_detected(self, accuracy_history: List[float], window: int = None) -> bool:
        if window is None:
            window = self.plateau_window
        if len(accuracy_history) < window:
            return False
        recent = accuracy_history[-window:]
        if len(recent) < 2:
            return False
        differences = [abs(recent[i] - recent[i + 1]) for i in range(len(recent) - 1)]
        avg_diff = sum(differences) / len(differences)
        return avg_diff < 0.03

    def set_plateau_window(self, window: int) -> None:
        self.plateau_window = max(2, window)

    def set_unlock_threshold(self, threshold: float) -> None:
        self.unlock_threshold = max(0.0, min(1.0, threshold))
