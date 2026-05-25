"""Tests for cost estimator."""

from nicto_neural.neural.config import NeuralConfig
from nicto_neural.evolution.cost_estimator import CostEstimator


def test_training_cost_estimate():
    config = NeuralConfig()
    estimator = CostEstimator(config)
    result = estimator.estimate_training_cost(dataset_size=1000, epochs=10)
    assert result["total_batches"] > 0
    assert result["estimated_flops"] > 0
    assert result["estimated_seconds"] > 0


def test_benchmark():
    config = NeuralConfig()
    estimator = CostEstimator(config)
    result = estimator.benchmark(lambda: sum(range(1000)), n_iterations=3)
    assert result["iterations"] == 3
    assert result["avg_seconds"] > 0


def test_param_estimation():
    config = NeuralConfig()
    estimator = CostEstimator(config)
    params = estimator._estimate_params()
    assert params > 0
