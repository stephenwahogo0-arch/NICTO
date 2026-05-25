"""Tests for exploration manager."""

from nicto_neural.neural.config import NeuralConfig
from nicto_neural.neural.exploration import ExplorationManager


def test_epsilon_decay():
    config = NeuralConfig()
    config.epsilon_start = 1.0
    config.epsilon_end = 0.01
    config.epsilon_decay = 100
    explorer = ExplorationManager(config)
    initial_eps = explorer.get_epsilon()
    for _ in range(50):
        explorer.should_explore()
    assert explorer.get_epsilon() < initial_eps


def test_epsilon_reaches_minimum():
    config = NeuralConfig()
    config.epsilon_start = 1.0
    config.epsilon_end = 0.01
    config.epsilon_decay = 10
    explorer = ExplorationManager(config)
    for _ in range(100):
        explorer.should_explore()
    assert explorer.get_epsilon() == 0.01


def test_get_stats():
    config = NeuralConfig()
    explorer = ExplorationManager(config)
    stats = explorer.get_stats()
    assert "epsilon" in stats
    assert "steps" in stats
    assert "noise_std" in stats
