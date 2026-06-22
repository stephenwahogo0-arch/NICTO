from typing import Any, Dict, List, Tuple
from dataclasses import dataclass, field
import time


@dataclass
class HackingRecord:
    brain: str
    reason: str
    timestamp: float
    suspicion_score: float = 0.0


class RewardHackingDetector:
    def __init__(self):
        self._records: List[HackingRecord] = []
        self._suspicion_scores: Dict[str, List[float]] = {}

    def detect(self, reward_history: List[float], quality_history: List[float]) -> Tuple[bool, float]:
        if len(reward_history) < 5 or len(quality_history) < 5:
            return False, 0.0
        recent_rewards = reward_history[-5:]
        recent_quality = quality_history[-5:]
        reward_trend = recent_rewards[-1] - recent_rewards[0]
        quality_trend = recent_quality[-1] - recent_quality[0]
        if reward_trend > 0.5 and quality_trend < 0.05:
            return True, self._compute_score(reward_trend, quality_trend)
        variance = 0.0
        if len(reward_history) >= 3:
            mean_r = sum(reward_history[-3:]) / 3
            variance = sum((r - mean_r) ** 2 for r in reward_history[-3:]) / 3
        if variance < 0.01 and quality_trend < -0.1:
            return True, 0.7
        return False, 0.0

    def _compute_score(self, reward_trend: float, quality_trend: float) -> float:
        score = min(1.0, abs(reward_trend) / max(abs(quality_trend) + 0.01, 0.01))
        return min(1.0, score * 0.5)

    def score_suspicion(self, history: List[Dict]) -> float:
        if not history:
            return 0.0
        rewards = [h.get("reward", 0) for h in history]
        qualities = [h.get("quality", 0) for h in history]
        _, score = self.detect(rewards, qualities)
        return score

    def flag_hacking(self, brain: str, reason: str):
        record = HackingRecord(brain=brain, reason=reason, timestamp=time.time())
        self._records.append(record)
        if brain not in self._suspicion_scores:
            self._suspicion_scores[brain] = []
        self._suspicion_scores[brain].append(record.suspicion_score)

    def get_flags(self, brain: str = None) -> List[HackingRecord]:
        if brain:
            return [r for r in self._records if r.brain == brain]
        return self._records

    def clear_flags(self, brain: str = None):
        if brain:
            self._records = [r for r in self._records if r.brain != brain]
            self._suspicion_scores.pop(brain, None)
        else:
            self._records.clear()
            self._suspicion_scores.clear()