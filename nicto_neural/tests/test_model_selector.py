import pytest
from ..neural.model_selector import ModelSelector, ModelComplexity


def test_small_dataset():
    ms = ModelSelector()
    selection = ms.select(dataset_size=50, domain="code")
    assert selection.model_type == ModelComplexity.BOOST_FIXED


def test_medium_dataset():
    ms = ModelSelector()
    selection = ms.select(dataset_size=500, domain="code")
    assert selection.model_type == ModelComplexity.BOOST_TRAINED


def test_large_dataset():
    ms = ModelSelector()
    selection = ms.select(dataset_size=5000, domain="code")
    assert selection.model_type == ModelComplexity.TRANSFORMER


def test_interpretability_override():
    ms = ModelSelector()
    selection = ms.select(dataset_size=5000, domain="code", require_interpretability=True)
    assert selection.model_type != ModelComplexity.TRANSFORMER


def test_time_budget():
    ms = ModelSelector()
    selection = ms.select(dataset_size=5000, domain="code", time_budget_minutes=5)
    assert selection.estimated_time_minutes <= 15.0


def test_history():
    ms = ModelSelector()
    ms.select(dataset_size=50, domain="code")
    ms.select(dataset_size=500, domain="math")
    assert len(ms.get_selection_history()) == 2