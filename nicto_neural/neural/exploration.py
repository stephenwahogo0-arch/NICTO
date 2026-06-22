import math
import random
import torch
import numpy as np
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ExplorationSchedule:
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.9995
    noise_scale: float = 0.1
    noise_decay: float = 0.999
    temperature_start: float = 1.0
    temperature_end: float = 0.1
    temperature_decay: float = 0.999
    total_steps: int = 100000


class ExplorationEngine:
    def __init__(self, schedule: Optional[ExplorationSchedule] = None):
        self.schedule = schedule or ExplorationSchedule()
        self.step_count: int = 0
        self.per_brain_epsilon: Dict[str, float] = {}
        self.per_brain_temperature: Dict[str, float] = {}
        self.per_brain_noise: Dict[str, float] = {}

    def current_epsilon(self, brain: Optional[str] = None) -> float:
        if brain and brain in self.per_brain_epsilon:
            return self.per_brain_epsilon[brain]
        eps = self.schedule.epsilon_end + (
            self.schedule.epsilon_start - self.schedule.epsilon_end
        ) * math.exp(-self.step_count * self.schedule.epsilon_decay)
        return max(self.schedule.epsilon_end, eps)

    def current_temperature(self, brain: Optional[str] = None) -> float:
        if brain and brain in self.per_brain_temperature:
            return self.per_brain_temperature[brain]
        temp = self.schedule.temperature_end + (
            self.schedule.temperature_start - self.schedule.temperature_end
        ) * math.exp(-self.step_count * self.schedule.temperature_decay)
        return max(self.schedule.temperature_end, temp)

    def current_noise_scale(self, brain: Optional[str] = None) -> float:
        if brain and brain in self.per_brain_noise:
            return self.per_brain_noise[brain]
        return self.schedule.noise_scale * (self.schedule.noise_decay ** self.step_count)

    def should_explore(self, brain: Optional[str] = None) -> bool:
        return random.random() < self.current_epsilon(brain)

    def add_action_noise(self, action: torch.Tensor, brain: Optional[str] = None) -> torch.Tensor:
        scale = self.current_noise_scale(brain)
        noise = torch.randn_like(action) * scale
        return action + noise

    def add_weight_noise(self, weights: torch.Tensor, brain: Optional[str] = None) -> torch.Tensor:
        scale = self.current_noise_scale(brain) * 0.1
        noise = torch.randn_like(weights[:weights.size(0) // 2]) * scale if weights.size(0) > 1 else torch.randn_like(weights) * scale
        return weights

    def temperature_softmax(self, logits: torch.Tensor, brain: Optional[str] = None) -> torch.Tensor:
        temp = self.current_temperature(brain)
        return torch.softmax(logits / max(temp, 1e-6), dim=-1)

    def greedy_action(self, logits: torch.Tensor) -> torch.Tensor:
        return torch.argmax(logits, dim=-1)

    def sample_action(self, logits: torch.Tensor, brain: Optional[str] = None) -> torch.Tensor:
        if self.should_explore(brain):
            probs = self.temperature_softmax(logits, brain)
            dist = torch.distributions.Categorical(probs)
            action = dist.sample()
        else:
            action = self.greedy_action(logits)
        return action

    def update_per_brain_epsilon(self, brain: str, epsilon: float):
        self.per_brain_epsilon[brain] = max(self.schedule.epsilon_end, min(self.schedule.epsilon_start, epsilon))

    def update_per_brain_temperature(self, brain: str, temperature: float):
        self.per_brain_temperature[brain] = max(self.schedule.temperature_end, min(self.schedule.temperature_start, temperature))

    def update_per_brain_noise(self, brain: str, noise_scale: float):
        self.per_brain_noise[brain] = max(0.0, noise_scale)

    def step(self):
        self.step_count += 1

    def reset(self):
        self.step_count = 0
        self.per_brain_epsilon.clear()
        self.per_brain_temperature.clear()
        self.per_brain_noise.clear()
