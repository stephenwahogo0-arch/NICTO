import pytest
import torch
from ..learning.rl_agent import RLAgent
from ..neural.config import NeuralConfig


def test_rl_agent_forward():
    config = NeuralConfig(d_model=64)
    agent = RLAgent(config, n_actions=10)
    state = torch.randn(1, 15)
    probs, value = agent(state)
    assert probs.shape == (1, 10)
    assert value.shape == (1, 1)