import pytest
import numpy as np
from ..reasoning.brainboost import BrainBoost


def test_fixed_mode():
    bb = BrainBoost(n_stages=3)
    outputs = {"primary": np.random.randn(10), "analytical": np.random.randn(10)}
    result = bb.predict(None, outputs, mode="fixed")
    assert result is not None


def test_trained_mode():
    bb = BrainBoost(n_stages=2)
    task_vectors = np.random.randn(1, 15)
    brain_outputs = [
        {"primary": np.random.randn(10), "analytical": np.random.randn(10)}
    ]
    targets = np.random.randn(10)
    try:
        bb.train_weights(task_vectors, brain_outputs, targets)
        trained = True
    except Exception as e:
        print(f"Error: {e}")
        trained = False
    assert trained


def test_regularization():
    bb = BrainBoost(n_stages=3, learning_rate=0.3)
    loss = bb.regularization_loss()
    assert loss >= 0.0