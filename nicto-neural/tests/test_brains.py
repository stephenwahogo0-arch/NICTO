"""Tests for the 6-brain system."""

import torch

from nicto_neural.neural.config import NeuralConfig
from nicto_neural.neural.elo_system import EloSystem
from nicto_neural.neural.exploration import ExplorationManager
from nicto_neural.brain.primary import PrimaryBrain
from nicto_neural.brain.analytical import AnalyticalBrain
from nicto_neural.brain.creative import CreativeBrain
from nicto_neural.brain.strategic import StrategicBrain
from nicto_neural.brain.knowledge import KnowledgeBrain
from nicto_neural.brain.intuitive import IntuitiveBrain


def test_primary_brain_routing():
    config = NeuralConfig()
    elo = EloSystem(config)
    brain = PrimaryBrain(config, elo)
    x = torch.randn(1, 8, config.d_model)
    result = brain(x)
    assert "routing" in result
    assert result["brain"] == "primary"


def test_analytical_brain():
    config = NeuralConfig()
    elo = EloSystem(config)
    brain = AnalyticalBrain(config, elo)
    x = torch.randn(1, 8, config.d_model)
    result = brain(x)
    assert "confidence" in result
    assert result["brain"] == "analytical"


def test_creative_brain():
    config = NeuralConfig()
    elo = EloSystem(config)
    brain = CreativeBrain(config, elo)
    x = torch.randn(1, 8, config.d_model)
    result = brain(x)
    assert result["brain"] == "creative"
    assert result["temperature"] == 0.8


def test_strategic_brain():
    config = NeuralConfig()
    elo = EloSystem(config)
    brain = StrategicBrain(config, elo)
    x = torch.randn(1, 8, config.d_model)
    result = brain(x)
    assert "priority" in result


def test_knowledge_brain():
    config = NeuralConfig()
    elo = EloSystem(config)
    brain = KnowledgeBrain(config, elo)
    x = torch.randn(1, 8, config.d_model)
    result = brain(x)
    assert "relevance" in result


def test_intuitive_brain():
    config = NeuralConfig()
    elo = EloSystem(config)
    explorer = ExplorationManager(config)
    brain = IntuitiveBrain(config, elo, explorer)
    x = torch.randn(1, 8, config.d_model)
    result = brain(x)
    assert "epsilon" in result
