"""Tests for learning modules."""

import tempfile

from nicto_neural.learning.reward_shaper import RewardShaper
from nicto_neural.learning.feedback_loop import FeedbackLoop
from nicto_neural.learning.dataset_builder import DatasetBuilder
from nicto_neural.memory.manager import MemoryManager
from nicto_neural.neural.config import NeuralConfig


def test_reward_shaper_shape():
    shaper = RewardShaper()
    result = shaper.shape(
        correctness=0.8,
        elo_delta=10.0,
        is_novel=True,
        consistency_score=0.7,
        hacking_detected=False,
    )
    assert result["total"] > 0
    assert result["creativity_bonus"] == 1.5
    assert result["hack_penalty"] == 0.0


def test_reward_shaper_hacking_penalty():
    shaper = RewardShaper()
    result = shaper.shape(
        correctness=0.5,
        hacking_detected=True,
    )
    assert result["hack_penalty"] == 10.0
    assert result["creativity_bonus"] == 0.0


def test_creativity_gate():
    shaper = RewardShaper()
    low = shaper.shape(correctness=0.3)
    high = shaper.shape(correctness=0.8)
    assert low["creativity_bonus"] == 0.0
    assert high["creativity_bonus"] == 1.5


def test_feedback_loop():
    loop = FeedbackLoop()
    loop.add_feedback("test task", quality=0.2, source="user")
    results = loop.process_batch()
    assert len(results) == 1
    assert results[0]["action"] == "retrain_domain"


def test_dataset_builder():
    config = NeuralConfig()
    config.memory_db_path = tempfile.mkdtemp()
    memory = MemoryManager(config)
    builder = DatasetBuilder(memory)
    result = builder.build(output_path=tempfile.mktemp(suffix=".jsonl"))
    assert result["deduplicated"] is True
