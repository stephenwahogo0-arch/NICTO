import pytest
from ..evolution.validation import ValidationEngine
from ..reasoning.evaluator import Evaluator
from ..neural.elo_system import ELOEstimator


def test_split():
    val = ValidationEngine(Evaluator(), ELOEstimator())
    dataset = [{"id": i} for i in range(100)]
    train, test = val.split(dataset, val_ratio=0.2)
    assert len(train) == 80
    assert len(test) == 20


def test_accuracy_report():
    val = ValidationEngine(Evaluator(), ELOEstimator())
    results = [
        {"correct": True, "domain": "code"},
        {"correct": True, "domain": "code"},
        {"correct": False, "domain": "math"},
    ]
    report = val.accuracy_report(results)
    assert "accuracy" in report


def test_per_domain():
    val = ValidationEngine(Evaluator(), ELOEstimator())
    results = [
        {"correct": True, "domain": "code"},
        {"correct": False, "domain": "math"},
    ]
    domain_acc = val.per_domain_accuracy(results)
    assert isinstance(domain_acc, dict)