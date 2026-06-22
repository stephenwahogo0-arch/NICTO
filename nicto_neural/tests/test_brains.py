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


def test_analytical():
    config = NeuralConfig(d_model=64)
    brain = AnalyticalBrain(config)
    x = torch.randn(1, 8, 64)
    output, confidence = brain(x)
    assert output.shape == (1, 8, 64)


def test_creative():
    config = NeuralConfig(d_model=64)
    brain = CreativeBrain(config)
    x = torch.randn(1, 8, 64)
    output, confidence = brain(x, temperature=0.8)
    assert output.shape == (1, 8, 64)
    assert confidence.shape == (1, 8, 1)


def test_analytical():
    config = NeuralConfig(d_model=64)
    brain = AnalyticalBrain(config)
    x = torch.randn(1, 8, 64)
    output, confidence = brain(x)
    assert output.shape[-1] == 64


def test_creative():
    config = NeuralConfig(d_model=64)
    brain = CreativeBrain(config)
    x = torch.randn(1, 8, 64)
    output, confidence = brain(x, temperature=0.8)
    assert output.shape[-1] == 64
    assert confidence is not None


def test_creative():
    config = NeuralConfig(d_model=64)
    brain = CreativeBrain(config)
    x = torch.randn(1, 8, 64)
    output, confidence = brain(x, temperature=0.8)
    assert output.shape[-1] == 64


def test_strategic():
    config = NeuralConfig(d_model=64)
    brain = StrategicBrain(config)
    x = torch.randn(1, 8, 64)
    output, confidence = brain(x)
    assert output is not None


def test_intuitive():
    config = NeuralConfig(d_model=64)
    brain = IntuitiveBrain(config)
    x = torch.randn(1, 8, 64)
    output, confidence = brain(x)
    assert output.shape == (1, 8, 64)