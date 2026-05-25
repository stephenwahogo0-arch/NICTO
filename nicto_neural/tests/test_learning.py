import pytest
from ..learning.dataset_builder import DatasetBuilder
from ..learning.reward_model import RewardModel
from ..learning.feedback_loop import FeedbackLoop


def test_reward_components():
    rm = RewardModel()
    comps = rm.reward_components(
        {"input": "test"}, "output", "expected",
        elo_delta=5.0, val_improvement=0.1, user_feedback=1.0,
        novelty=0.2, consistency=0.9, hacking_penalty=0.0,
    )
    assert isinstance(comps, dict)
    assert "correctness" in comps


def test_dataset_build():
    db = DatasetBuilder()
    dataset = db.from_conversations(limit=5)
    assert isinstance(dataset, list)


def test_dataset_split():
    db = DatasetBuilder()
    items = [{"id": i} for i in range(100)]
    train, val = db.train_val_split(items, val_ratio=0.2)
    assert len(train) == 80
    assert len(val) == 20


def test_trainer_init():
    from ..neural.config import NeuralConfig
    from ..learning.trainer import NeuralTrainer
    import torch.nn as nn
    config = NeuralConfig(d_model=64, vocab_size=100)
    model = nn.Linear(64, 100)
    trainer = NeuralTrainer(config, model, device="cpu")
    assert trainer is not None