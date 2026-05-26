"""Tests for model selector."""

from nicto_neural.neural.model_selector import ModelSelector


def test_small_dataset():
    selector = ModelSelector()
    assert selector.select(50) == "brainboost_fixed"


def test_medium_dataset():
    selector = ModelSelector()
    assert selector.select(5000) == "brainboost_trained"


def test_large_dataset():
    selector = ModelSelector()
    assert selector.select(50000) == "transformer_rl"


def test_path_info():
    selector = ModelSelector()
    info = selector.get_path_info("brainboost_fixed")
    assert "description" in info
    assert info["speed"] == "fast"
