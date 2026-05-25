"""Reward hacking detector — prevents reward gaming."""


class RewardHackingDetector:
    """Detects and prevents reward gaming inspired by Trackmania drift-spamming."""

    REPEAT_THRESHOLD = 5
    FLAT_QUALITY_TOLERANCE = 0.02
    MIN_REWARD_RISE_TO_FLAG = 0.1

    def __init__(self):
        self._action_history: list[int] = []
        self._quality_history: list[float] = []
        self._reward_history: list[float] = []
        self._flags: list[str] = []

    def check(
        self,
        action: int,
        quality: float,
        reward: float,
        task_completed: bool = True,
    ) -> dict:
        self._action_history.append(action)
        self._quality_history.append(quality)
        self._reward_history.append(reward)

        flags = []

        if len(self._quality_history) >= 5:
            recent_quality = self._quality_history[-5:]
            recent_reward = self._reward_history[-5:]
            quality_slope = (recent_quality[-1] - recent_quality[0]) / 5
            reward_slope = (recent_reward[-1] - recent_reward[0]) / 5

            if (abs(quality_slope) < self.FLAT_QUALITY_TOLERANCE
                    and reward_slope > self.MIN_REWARD_RISE_TO_FLAG):
                flags.append("flat_quality_rising_reward")

        if len(self._action_history) >= self.REPEAT_THRESHOLD:
            recent = self._action_history[-self.REPEAT_THRESHOLD:]
            if len(set(recent)) == 1:
                flags.append(f"action_{action}_repeated_{self.REPEAT_THRESHOLD}_times")

        if not task_completed and len(self._reward_history) >= 2:
            if self._reward_history[-1] > self._reward_history[-2]:
                flags.append("reward_increase_no_completion")

        is_hacking = len(flags) > 0
        if is_hacking:
            self._flags.extend(flags)

        return {
            "hacking_detected": is_hacking,
            "flags": flags,
            "total_flags": len(self._flags),
            "penalty": 10.0 if is_hacking else 0.0,
        }

    def get_stats(self) -> dict:
        return {
            "total_checks": len(self._action_history),
            "total_flags": len(self._flags),
            "flag_rate": len(self._flags) / max(len(self._action_history), 1),
            "recent_flags": self._flags[-5:],
        }
