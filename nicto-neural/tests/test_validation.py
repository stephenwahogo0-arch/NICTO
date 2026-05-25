"""Tests for validation engine."""

import tempfile

from nicto_neural.evolution.validation import ValidationEngine
from nicto_neural.memory.manager import MemoryManager
from nicto_neural.neural.config import NeuralConfig


def test_split():
    config = NeuralConfig()
    config.memory_db_path = tempfile.mkdtemp()
    memory = MemoryManager(config)
    engine = ValidationEngine(memory)
    dataset = [{"input": f"task_{i}"} for i in range(100)]
    train, hold_out = engine.split(dataset)
    assert len(train) == 80
    assert len(hold_out) == 20


def test_accuracy_trend():
    config = NeuralConfig()
    config.memory_db_path = tempfile.mkdtemp()
    memory = MemoryManager(config)
    engine = ValidationEngine(memory)
    assert engine.accuracy_trend() == "insufficient_data"
    engine._results = [0.5, 0.6, 0.7, 0.8]
    assert engine.accuracy_trend() == "improving"
