"""Tests for consistency tracker — sigma formula."""

from nicto_neural.reasoning.consistency import ConsistencyTracker


def test_logical_coherence():
    tracker = ConsistencyTracker()
    chain = ["A is true", "B follows from A", "C follows from B"]
    score = tracker.logical_coherence(chain)
    assert 0.0 <= score <= 1.0


def test_contradiction_detection():
    tracker = ConsistencyTracker()
    chain = ["X is true", "X is false"]
    score = tracker.logical_coherence(chain)
    assert score < 1.0


def test_sigma_formula():
    tracker = ConsistencyTracker()
    chain = ["step 1", "step 2", "step 3"]
    sigma = tracker.sigma(chain, "test_task", "output")
    assert 0.0 <= sigma <= 1.0


def test_output_stability():
    tracker = ConsistencyTracker()
    for _ in range(5):
        tracker.output_stability("same_task", "same output")
    score = tracker.output_stability("same_task", "same output")
    assert score == 1.0


def test_sigma_weights():
    tracker = ConsistencyTracker()
    chain = ["A is true", "A is false"]
    sigma = tracker.sigma(chain, "task", "output")
    coherence = tracker.logical_coherence(chain)
    stability = tracker.output_stability("task", "output")
    expected = 0.6 * coherence + 0.4 * stability
    assert abs(sigma - expected) < 0.2
