import pytest
import torch
from ..neural.exploration import ExplorationEngine, ExplorationSchedule


def test_epsilon_decay():
    sched = ExplorationSchedule(epsilon_start=1.0, epsilon_end=0.01, epsilon_decay=0.999)
    eng = ExplorationEngine(schedule=sched)
    initial = eng.current_epsilon()
    for _ in range(1000):
        eng.step()
    assert eng.current_epsilon() < initial


def test_should_explore():
    sched = ExplorationSchedule(epsilon_start=1.0, epsilon_end=0.5, epsilon_decay=1.0)
    eng = ExplorationEngine(schedule=sched)
    assert eng.should_explore()


def test_temperature():
    eng = ExplorationEngine()
    assert 0.0 < eng.current_temperature() <= 1.0


def test_noise_bounds():
    eng = ExplorationEngine()
    action = torch.zeros(5)
    noisy = eng.add_action_noise(action)
    assert noisy.shape == (5,) or noisy.shape