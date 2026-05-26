"""Tests for curriculum scheduler — plateau detection."""

from nicto_neural.learning.curriculum import CurriculumScheduler


def test_plateau_detection():
    sched = CurriculumScheduler()
    for _ in range(5):
        sched.record_accuracy("analytical", "math", 0.80)
    assert sched.should_unlock("analytical", "math") is True


def test_no_unlock_below_min():
    sched = CurriculumScheduler()
    for _ in range(5):
        sched.record_accuracy("analytical", "math", 0.60)
    assert sched.should_unlock("analytical", "math") is False


def test_level_progression():
    sched = CurriculumScheduler()
    for _ in range(4):
        sched.record_accuracy("primary", "general", 0.80)
    result = sched.record_accuracy("primary", "general", 0.80)
    assert result["unlocked"] is True
    assert result["new_level"] == 1


def test_no_plateau_when_improving():
    sched = CurriculumScheduler()
    for i in range(5):
        sched.record_accuracy("analytical", "code", 0.70 + i * 0.05)
    assert sched.should_unlock("analytical", "code") is False
