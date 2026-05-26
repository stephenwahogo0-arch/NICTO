"""Tests for PPO RL agent."""

import torch

from nicto_neural.neural.config import NeuralConfig
from nicto_neural.learning.rl_agent import PPOAgent


def test_ppo_update():
    config = NeuralConfig()
    agent = PPOAgent(config)
    batch = {
        "states": [torch.randn(15) for _ in range(16)],
        "actions": [0] * 16,
        "rewards": [1.0] * 16,
        "dones": [False] * 16,
        "log_probs": [0.0] * 16,
    }
    metrics = agent.update(batch)
    assert "policy_loss" in metrics
    assert "value_loss" in metrics
    assert "entropy" in metrics


def test_action_selection():
    config = NeuralConfig()
    agent = PPOAgent(config)
    state = torch.randn(15)
    action, log_prob = agent.select_action(state)
    assert 0 <= action < config.n_brains
    assert isinstance(log_prob, float)


def test_gae_computation():
    config = NeuralConfig()
    agent = PPOAgent(config)
    rewards = [1.0, 0.5, 0.8]
    values = [0.5, 0.6, 0.7]
    dones = [False, False, False]
    advantages = agent.compute_gae(rewards, values, dones)
    assert len(advantages) == 3
