import pytest
import numpy as np
from ..perception.feature_engine import FeatureEngine


def test_feature_dimensions():
    fe = FeatureEngine()
    task = {"input": "test", "type": "code", "domain": "math"}
    features = fe.extract(task)
    assert len(features) == 15


def test_feature_values():
    fe = FeatureEngine()
    task = {"input": "test", "type": "code", "domain": "math"}
    features = fe.extract(task)
    assert 0.0 <= features[0] <= 1.0  # task_type one-hot
    assert 0.0 <= features[1] <= 1.0  # domain
    assert features[2] >= 0.0          # complexity


def test_feature_names():
    fe = FeatureEngine()
    names = fe.feature_names()
    assert len(names) == 15


def test_default_task():
    fe = FeatureEngine()
    features = fe.extract({})
    assert len(features) == 15