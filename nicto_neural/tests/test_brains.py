import pytest
import torch
from ..neural.config import NeuralConfig
from ..brain.primary import PrimaryBrain
from ..brain.analytical import AnalyticalBrain
from ..brain.creative import CreativeBrain
from ..brain.strategic import StrategicBrain
from ..brain.intuitive import IntuitiveBrain


def test_primary():
    config = NeuralConfig(d_model=64)
    brain = PrimaryBrain(config)
    x = torch.randn(1, 8, 64)
    output, confidence = brain(x)
    assert output.shape == (1, 8, 64)
    assert confidence.shape == (1, 8, 1)
    assert confidence.min() >= 0.0
    assert confidence.max() <= 1.0


def test_analytical():
    config = NeuralConfig(d_model=64)
    brain = AnalyticalBrain(config)
    x = torch.randn(1, 8, 64)
    output, confidence = brain(x)
    assert output.shape == (1, 8, 64)
    assert confidence.shape == (1, 8, 1)
    assert confidence.min() >= 0.0


def test_creative():
    config = NeuralConfig(d_model=64)
    brain = CreativeBrain(config)
    x = torch.randn(1, 8, 64)
    output, confidence = brain(x, temperature=0.8)
    assert output.shape == (1, 8, 64)
    assert confidence.shape == (1, 8, 1)
    assert confidence.min() >= 0.0 and confidence.max() <= 1.0


def test_strategic():
    config = NeuralConfig(d_model=64)
    brain = StrategicBrain(config)
    x = torch.randn(1, 8, 64)
    output, confidence = brain(x)
    assert output.shape == (1, 8, 64)
    assert confidence.shape == (1, 8, 1)


def test_intuitive():
    config = NeuralConfig(d_model=64)
    brain = IntuitiveBrain(config)
    x = torch.randn(1, 8, 64)
    output, confidence = brain(x)
    assert output.shape == (1, 8, 64)
    assert confidence.shape == (1, 8, 1)


def test_brains_produce_different_outputs():
    config = NeuralConfig(d_model=64)
    x = torch.randn(1, 8, 64)
    out1, _ = PrimaryBrain(config)(x)
    out2, _ = AnalyticalBrain(config)(x)
    out3, _ = CreativeBrain(config)(x)
    out4, _ = StrategicBrain(config)(x)
    out5, _ = IntuitiveBrain(config)(x)
    outputs = [out1, out2, out3, out4, out5]
    for i, oi in enumerate(outputs):
        for j, oj in enumerate(outputs):
            if i < j:
                diff = (oi - oj).abs().mean().item()
                assert diff > 0.0, f"Brains {i} and {j} produce identical output"
