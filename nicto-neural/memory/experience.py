"""Experience memory — RL replay buffer (state, action, reward, next_state, done)."""

import torch


class ExperienceBuffer:
    """Replay buffer for PPO training with prioritized sampling."""

    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self._buffer: list[dict] = []
        self._priorities: list[float] = []
        self._pos = 0

    def add(
        self,
        state: torch.Tensor,
        action: int,
        reward: float,
        next_state: torch.Tensor,
        done: bool,
        log_prob: float = 0.0,
    ) -> None:
        experience = {
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "done": done,
            "log_prob": log_prob,
        }
        priority = abs(reward) + 1e-6

        if len(self._buffer) < self.capacity:
            self._buffer.append(experience)
            self._priorities.append(priority)
        else:
            self._buffer[self._pos] = experience
            self._priorities[self._pos] = priority
            self._pos = (self._pos + 1) % self.capacity

    def sample(self, batch_size: int) -> dict:
        """Sample batch with priority weighting."""
        import random

        if len(self._buffer) < batch_size:
            indices = list(range(len(self._buffer)))
        else:
            total = sum(self._priorities)
            probs = [p / total for p in self._priorities]
            indices = random.choices(
                range(len(self._buffer)), weights=probs, k=batch_size
            )

        batch: dict[str, list] = {
            "states": [],
            "actions": [],
            "rewards": [],
            "next_states": [],
            "dones": [],
            "log_probs": [],
        }
        for i in indices:
            exp = self._buffer[i]
            batch["states"].append(exp["state"])
            batch["actions"].append(exp["action"])
            batch["rewards"].append(exp["reward"])
            batch["next_states"].append(exp["next_state"])
            batch["dones"].append(float(exp["done"]))
            batch["log_probs"].append(exp["log_prob"])

        return batch

    def __len__(self) -> int:
        return len(self._buffer)

    def is_ready(self, min_size: int = 64) -> bool:
        return len(self._buffer) >= min_size

    def count(self) -> int:
        return len(self._buffer)
