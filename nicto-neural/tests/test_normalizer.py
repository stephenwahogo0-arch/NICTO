"""Tests for feature normalizer."""

import torch

from nicto_neural.perception.normalizer import FeatureNormalizer


def test_fit_transform():
    norm = FeatureNormalizer(n_features=15)
    features = [torch.randn(15) for _ in range(50)]
    norm.fit(features)
    transformed = norm.transform(features[0])
    assert transformed.shape == (15,)


def test_untrained_passthrough():
    norm = FeatureNormalizer(n_features=15)
    features = torch.randn(15)
    result = norm.transform(features)
    assert torch.allclose(result, features)


def test_inverse_transform():
    norm = FeatureNormalizer(n_features=15)
    features = [torch.randn(15) for _ in range(50)]
    norm.fit(features)
    transformed = norm.transform(features[0])
    restored = norm.inverse_transform(transformed)
    assert torch.allclose(features[0], restored, atol=1e-5)
