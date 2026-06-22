from typing import Dict


class RewardShaper:
    def __init__(self):
        self.progress_scale = 0.1
        self.creativity_scale = 0.15
        self.drift_scale = 0.1
        self.drift_threshold = 0.5

    def shape(self, reward: float, context: Dict) -> float:
        shaped = reward
        task_completion = context.get("task_completion", 0.0)
        creativity_score = context.get("creativity_score", 0.0)
        quality_gate = context.get("quality_gate", 0.7)
        proxy_metric = context.get("proxy_metric", 0.0)
        speed_threshold = context.get("speed_threshold", self.drift_threshold)
        suspicion_score = context.get("suspicion_score", 0.0)

        shaped += self.progress_bonus(task_completion)
        shaped += self.bonus_gate(
            self.creativity_bonus(creativity_score, quality_gate),
            creativity_score > quality_gate
        )
        shaped += self.bonus_gate(
            self.drift_bonus(proxy_metric, speed_threshold),
            proxy_metric > speed_threshold
        )
        shaped = self.anti_hacking(shaped, suspicion_score)
        return max(0.0, min(2.0, shaped))

    def progress_bonus(self, task_completion: float) -> float:
        if task_completion <= 0.0:
            return 0.0
        if task_completion >= 1.0:
            return self.progress_scale * 1.0
        return self.progress_scale * (1.0 - abs(task_completion - 0.5) * 2) ** 2

    def creativity_bonus(self, creativity_score: float, quality_gate: float = 0.7) -> float:
        if creativity_score <= quality_gate:
            return 0.0
        excess = creativity_score - quality_gate
        return self.creativity_scale * min(1.0, excess / (1.0 - quality_gate))

    def drift_bonus(self, proxy_metric: float, speed_threshold: float) -> float:
        if proxy_metric <= speed_threshold:
            return 0.0
        excess = proxy_metric - speed_threshold
        return self.drift_scale * min(1.0, excess / (1.0 - speed_threshold))

    def anti_hacking(self, reward: float, suspicion_score: float) -> float:
        if suspicion_score <= 0.0:
            return reward
        penalty = suspicion_score * 0.5
        return max(0.0, reward * (1.0 - penalty))

    def bonus_gate(self, bonus: float, gate_condition: bool) -> float:
        return bonus if gate_condition else 0.0
