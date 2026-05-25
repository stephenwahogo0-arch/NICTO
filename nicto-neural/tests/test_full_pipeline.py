"""Full pipeline integration test."""

import asyncio
import tempfile

from nicto_neural.neural.config import NeuralConfig
from nicto_neural.neural_core import NeuralCore


def test_full_pipeline():
    """End-to-end: init -> process -> train -> validate -> status."""
    config = NeuralConfig()
    config.memory_db_path = tempfile.mkdtemp()
    core = NeuralCore(config)

    result = asyncio.run(core.process("What is a SQL injection attack?"))
    assert "output" in result
    assert "confidence" in result
    assert "brains_used" in result
    assert "domain" in result

    train_result = core.train(mode="rl", epochs=2)
    assert train_result["mode"] == "rl"

    status = core.get_status()
    assert status["version"] == "1.0.0"
    assert status["parameters"] == "284B+ (MoE architecture)"
    assert status["think_count"] >= 1
    assert status["initialized"] is True


def test_multi_process():
    """Process multiple inputs sequentially."""
    config = NeuralConfig()
    config.memory_db_path = tempfile.mkdtemp()
    core = NeuralCore(config)

    tasks = [
        "Explain SQL injection",
        "Write a Python sort function",
        "Plan a marketing strategy",
    ]
    for task in tasks:
        result = asyncio.run(core.process(task))
        assert result["confidence"] > 0

    assert core.consciousness._think_count == 3


def test_consistency_tracking():
    """Consistency tracker runs on chain-of-thought."""
    config = NeuralConfig()
    config.memory_db_path = tempfile.mkdtemp()
    core = NeuralCore(config)

    chain = ["Step 1: Identify the problem", "Step 2: Analyze solutions"]
    sigma = core.consistency.sigma(chain, "test_task", "test_output")
    assert 0.0 <= sigma <= 1.0


def test_reward_shaping():
    """Reward shaper correctly gates creativity bonus."""
    config = NeuralConfig()
    config.memory_db_path = tempfile.mkdtemp()
    core = NeuralCore(config)

    high = core.reward_shaper.shape(correctness=0.9)
    low = core.reward_shaper.shape(correctness=0.3)
    assert high["creativity_bonus"] == 1.5
    assert low["creativity_bonus"] == 0.0


def test_elo_system_integration():
    """ELO updates happen after processing."""
    config = NeuralConfig()
    config.memory_db_path = tempfile.mkdtemp()
    core = NeuralCore(config)

    asyncio.run(core.process("Solve 2+2"))
    leaderboard = core.elo.get_leaderboard("general")
    assert len(leaderboard) == len(config.brain_names)
