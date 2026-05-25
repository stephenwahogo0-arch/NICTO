import pytest
from ..learning.experience_buffer import ExperienceBuffer


def test_add_and_size():
    buf = ExperienceBuffer(capacity=100)
    s = [0.1] * 15
    ns = [0.2] * 15
    buf.add(s, 1, 1.0, ns, False)
    assert len(buf) == 1


def test_sample():
    buf = ExperienceBuffer(capacity=100)
    s = [0.1] * 15
    ns = [0.2] * 15
    for _ in range(50):
        buf.add(s, 1, 1.0, ns, False)
    batch = buf.sample(batch_size=10)
    assert len(batch) >= 5


def test_clear():
    buf = ExperienceBuffer(capacity=100)
    s = [0.1] * 15
    ns = [0.2] * 15
    buf.add(s, 1, 1.0, ns, False)
    buf.clear()
    assert len(buf) == 0


def test_capacity_limit():
    buf = ExperienceBuffer(capacity=10)
    s = [0.1] * 15
    ns = [0.2] * 15
    for _ in range(20):
        buf.add(s, 1, 1.0, ns, False)
    assert len(buf) <= 10
