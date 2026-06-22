import pytest
from ..learning.curriculum import Curriculum


def test_initial_level():
    c = Curriculum()
    assert c.get_level("primary", "code") == 0


def test_set_level():
    c = Curriculum()
    c.set_level("primary", "code", 3)
    assert c.get_level("primary", "code") == 3


def test_plateau_detection():
    c = Curriculum()
    history = [0.75, 0.76, 0.75, 0.77, 0.76]
    assert c.plateau_detected(history, window=3)


def test_no_plateau():
    c = Curriculum()
    history = [0.5, 0.6, 0.7, 0.8, 0.85]
    assert not c.plateau_detected(history, window=3)


def test_should_unlock():
    c = Curriculum()
    history = [0.76] * 5
    assert c.should_unlock("primary", "code", history)


def test_should_not_unlock_low():
    c = Curriculum()
    history = [0.6] * 5
    assert not c.should_unlock("primary", "code", history)