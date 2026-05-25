"""Tests for NeuralCore top-level facade."""

import asyncio
import tempfile

from nicto_neural.neural.config import NeuralConfig
from nicto_neural.neural_core import NeuralCore


def test_initialization():
    config = NeuralConfig()
    config.memory_db_path = tempfile.mkdtemp()
    core = NeuralCore(config)
    assert core._initialized is True
    assert core.VERSION == "1.0.0"


def test_process():
    config = NeuralConfig()
    config.memory_db_path = tempfile.mkdtemp()
    core = NeuralCore(config)
    result = asyncio.run(core.process("What is 2+2?"))
    assert "output" in result
    assert "confidence" in result
    assert "reward" in result


def test_get_status():
    config = NeuralConfig()
    config.memory_db_path = tempfile.mkdtemp()
    core = NeuralCore(config)
    status = core.get_status()
    assert status["version"] == "1.0.0"
    assert status["parameters"] == "284B+ (MoE architecture)"
    assert status["initialized"] is True


def test_train():
    config = NeuralConfig()
    config.memory_db_path = tempfile.mkdtemp()
    core = NeuralCore(config)
    result = core.train(mode="rl", epochs=2)
    assert result["mode"] == "rl"
