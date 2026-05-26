import math
import random
from typing import Dict


class ExplorationEngine:
    def __init__(self, epsilon_start: float = 1.0, epsilon_end: float = 0.01, decay_steps: int = 10000):
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.decay_steps = decay_steps
        self._step = 0
        self.epsilons: Dict[str, float] = {}

    def current_epsilon(self, brain: str) -> float:
        return self.epsilons.get(brain, self.epsilon_start)

    def should_explore(self) -> bool:
        eps = self.epsilon_end + (self.epsilon_start - self.epsilon_end) * math.exp(-self._step / (self.decay_steps / 5))
        return random.random() < eps

    def step(self) -> None:
        self._step += 1

    def current_temperature(self, brain: str) -> float:
        eps = self.current_epsilon(brain)
        return max(0.1, 1.0 - eps)

    def set_epsilon(self, brain: str, epsilon: float) -> None:
        self.epsilons[brain] = max(self.epsilon_end, min(self.epsilon_start, epsilon))

    def reset(self) -> None:
        self._step = 0
        self.epsilons.clear()
