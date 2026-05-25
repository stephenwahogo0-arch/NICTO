import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Dict, List, Optional, Tuple


class RLAgent(nn.Module):
    def __init__(self, config, n_actions: int = 10):
        super().__init__()
        self.config = config
        self.n_actions = n_actions
        self.device = torch.device(config.device if torch.cuda.is_available() and config.device == "cuda" else "cpu")
        self.shared = nn.Sequential(
            nn.Linear(15, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
        )
        self.actor = nn.Linear(128, n_actions)
        self.critic = nn.Linear(128, 1)
        self.to(self.device)
        self._log_probs: List[torch.Tensor] = []
        self._values: List[torch.Tensor] = []

    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        features = self.shared(state)
        action_probs = torch.softmax(self.actor(features), dim=-1)
        value = self.critic(features)
        return action_probs, value

    def get_action(self, state: np.ndarray, explore: bool = True) -> Tuple[int, torch.Tensor, torch.Tensor]:
        state_t = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
        action_probs, value = self.forward(state_t)
        dist = torch.distributions.Categorical(action_probs)
        if explore:
            action = dist.sample()
        else:
            action = action_probs.argmax(dim=-1)
        log_prob = dist.log_prob(action)
        return action.item(), log_prob, value

    def train_step(self, states: List[np.ndarray], actions: List[int], rewards: List[float],
                   next_states: List[np.ndarray], dones: List[bool], old_log_probs: List[torch.Tensor],
                   gamma: float = 0.99, gae_lambda: float = 0.95, clip_epsilon: float = 0.2,
                   entropy_coef: float = 0.01, value_coef: float = 0.5,
                   epochs: int = 10, lr: float = 3e-5) -> Dict:
        n = len(states)
        if n == 0:
            return {"policy_loss": 0.0, "value_loss": 0.0, "entropy": 0.0, "total_loss": 0.0}

        states_t = torch.tensor(np.array(states), dtype=torch.float32, device=self.device)
        actions_t = torch.tensor(actions, dtype=torch.long, device=self.device)
        rewards_t = torch.tensor(rewards, dtype=torch.float32, device=self.device)
        next_states_t = torch.tensor(np.array(next_states), dtype=torch.float32, device=self.device)
        dones_t = torch.tensor(dones, dtype=torch.float32, device=self.device)
        old_log_probs_t = torch.tensor([l.item() if isinstance(l, torch.Tensor) else l for l in old_log_probs],
                                        dtype=torch.float32, device=self.device)

        with torch.no_grad():
            _, next_values = self.forward(next_states_t)
            _, values = self.forward(states_t)
            next_values = next_values.squeeze(-1)
            values = values.squeeze(-1)
            deltas = rewards_t + gamma * next_values * (1.0 - dones_t) - values
            advantages = torch.zeros(n, device=self.device)
            gae = 0.0
            for t in reversed(range(n)):
                gae = deltas[t] + gamma * gae_lambda * (1.0 - dones_t[t]) * gae
                advantages[t] = gae
            returns = advantages + values

        optimizer = optim.AdamW(self.parameters(), lr=lr)
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0

        for _ in range(epochs):
            action_probs, values_pred = self.forward(states_t)
            values_pred = values_pred.squeeze(-1)
            dist = torch.distributions.Categorical(action_probs)
            new_log_probs = dist.log_prob(actions_t)
            entropy = dist.entropy().mean()

            ratio = torch.exp(new_log_probs - old_log_probs_t)
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1.0 - clip_epsilon, 1.0 + clip_epsilon) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()

            value_loss = nn.MSELoss()(values_pred, returns)

            loss = policy_loss + value_coef * value_loss - entropy_coef * entropy

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.parameters(), 1.0)
            optimizer.step()

            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            total_entropy += entropy.item()

        avg_policy = total_policy_loss / epochs
        avg_value = total_value_loss / epochs
        avg_entropy = total_entropy / epochs

        return {
            "policy_loss": avg_policy,
            "value_loss": avg_value,
            "entropy": avg_entropy,
            "total_loss": avg_policy + value_coef * avg_value - entropy_coef * avg_entropy,
        }

    def save(self, path: str) -> None:
        import os
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        torch.save({
            "model_state": self.state_dict(),
            "n_actions": self.n_actions,
        }, path)

    def load(self, path: str) -> None:
        state = torch.load(path, map_location=self.device)
        self.load_state_dict(state["model_state"])
        self.n_actions = state.get("n_actions", self.n_actions)
