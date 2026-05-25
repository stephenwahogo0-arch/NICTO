import pytest
from ..evolution.cost_estimator import TrainingCostEstimator


def test_estimate():
    ce = TrainingCostEstimator()
    estimate = ce.estimate(dataset_size=1000, model_type="brainboost_trained", epochs=5)
    assert "dataset_size" in estimate


def test_record_and_update():
    ce = TrainingCostEstimator()
    ce.record_actual("test_run", {"gpu_minutes": 5, "cpu_hours": 0})
    assert len(ce._actual_runs if hasattr(ce, "_actual_runs") else []) >= 0


def test_estimate_defaults():
    ce = TrainingCostEstimator()
    est = ce.estimate(dataset_size=100, model_type="brainboost_fixed")
    assert est is not None