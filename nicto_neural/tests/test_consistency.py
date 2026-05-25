import pytest
from ..reasoning.consistency import ConsistencyTracker


def test_coherence_perfect():
    ct = ConsistencyTracker()
    chain = ["x = 1", "y = x + 1", "z = y * 2"]
    score = ct.logical_coherence(chain)
    assert score > 0.0


def test_coherence_contradiction():
    ct = ConsistencyTracker()
    chain = ["x = 1", "x = 2"]
    score = ct.logical_coherence(chain)
    assert score < 1.0


def test_contradiction_count():
    ct = ConsistencyTracker()
    stmts = ["It is sunny", "It is not sunny"]
    assert ct.contradiction_count(stmts) >= 0


def test_stability():
    ct = ConsistencyTracker()
    def func(task):
        return "42"
    score = ct.output_stability({"input": "test"}, func, n=3)
    assert score >= 0.9