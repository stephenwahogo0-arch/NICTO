"""Tests for task feature engine."""

import torch

from nicto_neural.perception.feature_engine import TaskFeatureEngine


def test_feature_extraction():
    engine = TaskFeatureEngine()
    features = engine.extract("Write a Python function to sort a list")
    assert features.shape == (15,)


def test_feature_dimensions():
    engine = TaskFeatureEngine()
    features = engine.extract("Calculate the square root of 144", {"reasoning_depth": 3})
    assert features[3] == 3.0


def test_domain_detection():
    engine = TaskFeatureEngine()
    assert engine._detect_domain("hack the system") == "cybersecurity"
    assert engine._detect_domain("solve the equation") == "math"
    assert engine._detect_domain("write python code") == "code"


def test_task_type_detection():
    engine = TaskFeatureEngine()
    assert engine._detect_task_type("implement a function") == "code"
    assert engine._detect_task_type("create a poem") == "creative"
    assert engine._detect_task_type("analyze the data") == "analyze"


def test_complexity_estimation():
    engine = TaskFeatureEngine()
    simple = engine._estimate_complexity("hello")
    complex_task = engine._estimate_complexity(" ".join(["word"] * 100))
    assert complex_task > simple
