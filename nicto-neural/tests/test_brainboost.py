"""Tests for BrainBoost gradient-boosted ensemble."""

import torch

from nicto_neural.neural.config import NeuralConfig
from nicto_neural.brain.consciousness import NeuralConsciousness
from nicto_neural.reasoning.brainboost import BrainBoost


def test_ensemble_produces_output():
    config = NeuralConfig()
    consciousness = NeuralConsciousness(config)
    boost = BrainBoost(config, consciousness.brains)
    x = torch.randn(1, 8, config.d_model)
    result = boost.predict(x, mode="fixed")
    assert result["output"] is not None
    assert result["confidence"] > 0


def test_dual_mode():
    config = NeuralConfig()
    consciousness = NeuralConsciousness(config)
    boost = BrainBoost(config, consciousness.brains)
    x = torch.randn(1, 8, config.d_model)
    fixed = boost.predict(x, mode="fixed")
    assert fixed["mode"] == "fixed"
    trained = boost.predict(x, mode="trained")
    assert trained["mode"] == "trained"


def test_min_child_weight_gate():
    config = NeuralConfig()
    config.boost_min_child_weight = 0.99
    consciousness = NeuralConsciousness(config)
    boost = BrainBoost(config, consciousness.brains)
    x = torch.randn(1, 8, config.d_model)
    result = boost.predict(x, mode="fixed")
    assert result["stages"] >= 1
