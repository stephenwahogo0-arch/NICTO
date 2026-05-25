import pytest
import torch
from ..neural_core import NeuralCore
from ..neural.config import NeuralConfig


def test_full_pipeline():
    config = NeuralConfig(d_model=64, vocab_size=100)
    core = NeuralCore(config=config)
    task = {"input": "what is 2+2?", "domain": "math", "type": "question"}
    result = core.process(task)
    assert result is not None


def test_reflect():
    config = NeuralConfig(d_model=64, vocab_size=100)
    core = NeuralCore(config=config)
    task = {"input": "test", "domain": "general"}
    result = {"output": "test", "correct": True}
    reflection = core.reflect(task, result)
    assert reflection is not None
