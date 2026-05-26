"""PPO Agent — Proximal Policy Optimization for brain training."""

import torch
import torch.nn as nn
import torch.nn.functional as F


class PPOAgent:
    """PPO with clipped surrogate objective for brain selection policy."""

    def __init__(self, config, state_dim: int = 15, action_dim: int = 6):
        self.config = config
        self.state_dim = state_dim
        self.action_dim = action_dim

        self.policy = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim),
        )

        self.value = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
        )

        self.optimizer = torch.optim.Adam(
            list(self.policy.parameters()) + list(self.value.parameters()),
            lr=config.learning_rate,
        )

        self.clip_epsilon = config.ppo_clip
        self.ppo_epochs = config.ppo_epochs
        self.gae_lambda = config.gae_lambda
        self.value_coef = config.value_coef
        self.entropy_coef = config.entropy_coef
        self.gamma = 0.99

    def select_action(self, state: torch.Tensor) -> tuple[int, float]:
        """Select brain to activate."""
        with torch.no_grad():
            logits = self.policy(state)
            probs = F.softmax(logits, dim=-1)
            dist = torch.distributions.Categorical(probs)
            action = dist.sample()
            log_prob = dist.log_prob(action)
        return int(action), float(log_prob)

    def compute_gae(
        self, rewards: list, values: list, dones: list
    ) -> list:
        """Generalized Advantage Estimation."""
        advantages = []
        gae = 0.0
        next_value = 0.0

        for r, v, done in zip(reversed(rewards), reversed(values), reversed(dones)):
            delta = r + self.gamma * next_value * (1 - done) - v
            gae = delta + self.gamma * self.gae_lambda * (1 - done) * gae
            advantages.insert(0, gae)
            next_value = v

        return advantages

    def update(self, batch: dict) -> dict:
        """PPO update from experience batch."""
        states = torch.stack(batch["states"])
        actions = torch.tensor(batch["actions"])
        old_log_probs = torch.tensor(batch["log_probs"])
        rewards = batch["rewards"]
        dones = batch["dones"]

        with torch.no_grad():
            values = self.value(states).squeeze(-1).tolist()

        advantages = self.compute_gae(rewards, values, dones)
        advantages = torch.tensor(advantages, dtype=torch.float32)
        adv_std = advantages.std()
        if adv_std > 1e-8:
            advantages = (advantages - advantages.mean()) / (adv_std + 1e-8)

        returns = advantages + torch.tensor(values)

        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0

        for _ in range(self.ppo_epochs):
            logits = self.policy(states)
            probs = F.softmax(logits, dim=-1)
            dist = torch.distributions.Categorical(probs)

            new_log_probs = dist.log_prob(actions)
            entropy = dist.entropy().mean()

            ratio = (new_log_probs - old_log_probs).exp()
            surr1 = ratio * advantages
            surr2 = torch.clamp(
                ratio, 1.0 - self.clip_epsilon, 1.0 + self.clip_epsilon
            ) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()

            current_values = self.value(states).squeeze(-1)
            value_loss = F.mse_loss(current_values, returns)

            loss = (
                policy_loss
                + self.value_coef * value_loss
                - self.entropy_coef * entropy
            )

            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                list(self.policy.parameters()) + list(self.value.parameters()),
                self.config.grad_clip,
            )
            self.optimizer.step()

            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            total_entropy += entropy.item()

        return {
            "policy_loss": total_policy_loss / self.ppo_epochs,
            "value_loss": total_value_loss / self.ppo_epochs,
            "entropy": total_entropy / self.ppo_epochs,
        }
