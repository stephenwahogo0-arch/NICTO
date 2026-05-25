"""Tests for interpretability engine."""

import torch

from nicto_neural.reasoning.interpretability import InterpretabilityEngine


def test_explain_decision():
    engine = InterpretabilityEngine()
    result = engine.explain_decision(
        task="Write a Python function",
        brains_used=["analytical", "primary"],
        confidences={"analytical": 0.9, "primary": 0.6},
        domain="code",
        reasoning_chain=["Understand task", "Plan implementation", "Write code"],
    )
    assert result["primary_brain"] == "analytical"
    assert result["transparency_score"] > 0


def test_feature_importance():
    engine = InterpretabilityEngine()
    features = torch.tensor([0.5, 0.3, 0.8, 0.1, 0.2, 0.0, 0.4, 0.6, 0.9, 0.1, 0.7, 0.3, 0.2, 0.5, 0.0])
    importance = engine.feature_importance(features)
    assert len(importance) == 15
    assert sum(importance.values()) > 0.99


def test_average_transparency():
    engine = InterpretabilityEngine()
    assert engine.average_transparency() == 0.0
    engine.explain_decision(
        task="test",
        brains_used=["primary"],
        confidences={"primary": 0.8},
        domain="general",
    )
    assert engine.average_transparency() > 0
