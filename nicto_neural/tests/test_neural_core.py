import pytest
import torch
from ..neural_core import NeuralCore
from ..neural.config import NeuralConfig


def test_neural_core_init():
    config = NeuralConfig(d_model=64, vocab_size=100)
    core = NeuralCore(config=config)
    assert core.config.d_model == 64
    assert core.consciousness is not None


def test_neural_core_process():
    config = NeuralConfig(d_model=64, vocab_size=100)
    core = NeuralCore(config=config)
    task = {"input": "test", "domain": "general"}
    result = core.process(task)
    assert result is not None


def test_neural_core_has_apis():
    config = NeuralConfig(d_model=64)
    core = NeuralCore(config=config)
    assert "brain" in core.api
    assert "memory" in core.api
    assert "agent" in core.api
    assert "elo" in core.api
