import json
import os
import random
import numpy as np
from typing import Any, Dict, List, Optional, Tuple


class ExperienceBuffer:
    def __init__(self, capacity: int = 100000):
        self.capacity = capacity
        self.states: List[np.ndarray] = []
        self.actions: List[int] = []
        self.rewards: List[float] = []
        self.next_states: List[np.ndarray] = []
        self.dones: List[bool] = []
        self.priorities: List[float] = []
        self._index = 0
        self._size = 0

    def add(self, state: Any, action: int, reward: float, next_state: Any, done: bool, priority: float = 1.0) -> None:
        if isinstance(state, list):
            state = np.array(state, dtype=np.float32)
        if isinstance(next_state, list):
            next_state = np.array(next_state, dtype=np.float32)
        if len(self.states) < self.capacity:
            self.states.append(state)
            self.actions.append(action)
            self.rewards.append(reward)
            self.next_states.append(next_state)
            self.dones.append(done)
            self.priorities.append(priority)
        else:
            idx = self._index % self.capacity
            self.states[idx] = state
            self.actions[idx] = action
            self.rewards[idx] = reward
            self.next_states[idx] = next_state
            self.dones[idx] = done
            self.priorities[idx] = priority
        self._index += 1
        self._size = min(len(self.states), self.capacity)

    def sample(self, batch_size: int, alpha: float = 0.6) -> Tuple:
        n = len(self.states)
        if n == 0:
            return [], [], [], [], [], [], []
        batch_size = min(batch_size, n)
        probs = np.array(self.priorities[:n], dtype=np.float64) ** alpha
        probs_sum = probs.sum()
        if probs_sum <= 0:
            probs = np.ones(n, dtype=np.float64) / n
        else:
            probs = probs / probs_sum
        indices = list(np.random.choice(n, size=batch_size, replace=False, p=probs))
        batch_states = [self.states[i] for i in indices]
        batch_actions = [self.actions[i] for i in indices]
        batch_rewards = [self.rewards[i] for i in indices]
        batch_next_states = [self.next_states[i] for i in indices]
        batch_dones = [self.dones[i] for i in indices]
        batch_priorities = [self.priorities[i] for i in indices]
        batch_weights = [(1.0 / (n * probs[i])) for i in indices]
        max_w = max(batch_weights) if batch_weights else 1.0
        batch_weights = [w / max_w for w in batch_weights]
        return indices, batch_states, batch_actions, batch_rewards, batch_next_states, batch_dones, batch_weights

    def update_priorities(self, indices: List[int], priorities: List[float]) -> None:
        for idx, priority in zip(indices, priorities):
            if 0 <= idx < len(self.priorities):
                self.priorities[idx] = max(priority, 1e-6)

    def __len__(self) -> int:
        return self._size

    def clear(self) -> None:
        self.states.clear()
        self.actions.clear()
        self.rewards.clear()
        self.next_states.clear()
        self.dones.clear()
        self.priorities.clear()
        self._index = 0
        self._size = 0

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        data = {
            "states": [s.tolist() for s in self.states],
            "actions": self.actions,
            "rewards": self.rewards,
            "next_states": [ns.tolist() for ns in self.next_states],
            "dones": self.dones,
            "priorities": self.priorities,
            "index": self._index,
            "size": self._size,
        }
        with open(path, "w") as f:
            json.dump(data, f)

    def load(self, path: str) -> None:
        with open(path, "r") as f:
            data = json.load(f)
        self.states = [np.array(s, dtype=np.float32) for s in data["states"]]
        self.actions = data["actions"]
        self.rewards = data["rewards"]
        self.next_states = [np.array(ns, dtype=np.float32) for ns in data["next_states"]]
        self.dones = data["dones"]
        self.priorities = data["priorities"]
        self._index = data.get("index", len(self.states))
        self._size = data.get("size", len(self.states))
