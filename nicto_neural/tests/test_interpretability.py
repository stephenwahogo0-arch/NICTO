import pytest
from ..reasoning.interpretability import InterpretabilityReporter


def test_interpretability_score():
    ir = InterpretabilityReporter()
    task = {"input": "test", "type": "simple"}
    score = ir.score("primary", task, "output")
    assert 0.0 <= score <= 1.0


def test_report_creation():
    ir = InterpretabilityReporter()
    report = ir.report({"input": "test"}, "output", ["step1", "step2"], {"primary": 0.8})
    assert isinstance(report, str)
    assert len(report) > 0


def test_feature_attribution():
    ir = InterpretabilityReporter()
    import numpy as np
    fv = np.random.randn(15)
    attr = ir.feature_attribution(fv, "output")
    assert isinstance(attr, dict)