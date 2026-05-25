"""Tests for experience buffer."""

import torch

from nicto_neural.memory.experience import ExperienceBuffer


def test_add_and_sample():
    buf = ExperienceBuffer(capacity=100)
    for _ in range(20):
        buf.add(
            state=torch.randn(15),
            action=0,
            reward=1.0,
            next_state=torch.randn(15),
            done=False,
        )
    assert buf.count() == 20
    batch = buf.sample(8)
    assert len(batch["states"]) == 8


def test_is_ready():
    buf = ExperienceBuffer(capacity=100)
    assert buf.is_ready(10) is False
    for _ in range(10):
        buf.add(torch.randn(15), 0, 1.0, torch.randn(15), False)
    assert buf.is_ready(10) is True


def test_capacity_limit():
    buf = ExperienceBuffer(capacity=10)
    for i in range(20):
        buf.add(torch.randn(15), i % 6, float(i), torch.randn(15), False)
    assert buf.count() == 10
