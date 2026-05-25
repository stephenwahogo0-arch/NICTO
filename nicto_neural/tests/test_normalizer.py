import pytest
from ..perception.normalizer import FeatureNormalizer
import numpy as np


def test_normalize():
    normalizer = FeatureNormalizer(dim=3)
    data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    normalizer.fit(data)
    normalized = normalizer.normalize(np.array([[2.0, 3.0, 4.0]]))
    assert abs(normalized.mean()) < 1e-6 or abs(normalized[0, 0]) < 2.0


def test_partial_fit():
    normalizer = FeatureNormalizer(dim=2)
    normalizer.partial_fit(np.array([1.0, 2.0]))
    normalizer.partial_fit(np.array([3.0, 4.0]))
    normalized = normalizer.normalize(np.array([[2.0, 3.0]]))
    assert len(normalized[0]) == 2


def test_save_load():
    normalizer = FeatureNormalizer(dim=2)
    normalizer.partial_fit(np.array([1.0, 2.0]))
    normalizer.partial_fit(np.array([3.0, 4.0]))
    state = normalizer.state_dict()
    normalizer2 = FeatureNormalizer(dim=2)
    normalizer2.load_state_dict(state)
    assert normalizer2.mean[0] == normalizer.mean[0]
