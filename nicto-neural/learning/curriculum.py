"""Adaptive curriculum scheduler — plateau-based difficulty progression."""


class CurriculumScheduler:
    """Adaptive difficulty progression. Unlocks next level on plateau at >=75%."""

    LEVELS = {
        0: "single_step",
        1: "multi_step",
        2: "domain_depth",
        3: "cross_domain",
        4: "long_horizon",
        5: "meta_reasoning",
    }

    MAX_LEVEL = 5
    PLATEAU_WINDOW = 5
    PLATEAU_SLOPE_THRESHOLD = 0.01
    MIN_ACCURACY = 0.75

    def __init__(self):
        self._levels: dict[str, dict[str, int]] = {}
        self._accuracy_history: dict[tuple[str, str], list[float]] = {}

    def get_level(self, brain: str, domain: str) -> int:
        return self._levels.get(brain, {}).get(domain, 0)

    def get_level_name(self, brain: str, domain: str) -> str:
        level = self.get_level(brain, domain)
        return self.LEVELS.get(level, "unknown")

    def can_handle(self, brain: str, domain: str) -> bool:
        return True

    def record_accuracy(self, brain: str, domain: str, accuracy: float) -> dict:
        """Record accuracy and check if level should unlock."""
        key = (brain, domain)
        if key not in self._accuracy_history:
            self._accuracy_history[key] = []

        self._accuracy_history[key].append(accuracy)
        current_level = self.get_level(brain, domain)
        unlocked = False

        if self.should_unlock(brain, domain):
            if current_level < self.MAX_LEVEL:
                if brain not in self._levels:
                    self._levels[brain] = {}
                self._levels[brain][domain] = current_level + 1
                unlocked = True

        return {
            "brain": brain,
            "domain": domain,
            "current_level": current_level,
            "new_level": self.get_level(brain, domain),
            "unlocked": unlocked,
            "level_name": self.get_level_name(brain, domain),
        }

    def should_unlock(self, brain: str, domain: str) -> bool:
        """Adaptive plateau detection."""
        key = (brain, domain)
        history = self._accuracy_history.get(key, [])

        if len(history) < self.PLATEAU_WINDOW:
            return False

        recent = history[-self.PLATEAU_WINDOW:]
        mean_acc = sum(recent) / len(recent)

        if mean_acc < self.MIN_ACCURACY:
            return False

        n = len(recent)
        x_mean = (n - 1) / 2.0
        slope_num = sum(
            (i - x_mean) * (v - mean_acc) for i, v in enumerate(recent)
        )
        slope_den = sum((i - x_mean) ** 2 for i in range(n)) + 1e-8
        slope = slope_num / slope_den

        return abs(slope) < self.PLATEAU_SLOPE_THRESHOLD
