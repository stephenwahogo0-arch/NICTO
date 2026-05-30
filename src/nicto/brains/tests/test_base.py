"""Unit tests for brain base classes."""
from __future__ import annotations

import sys
import pytest
from pydantic import ValidationError

from src.nicto.brains.base import BrainConfig, BrainResponse, HardwareProfile


def test_hardware_profile_detection():
    """Test that hardware detection runs without error and returns sensible values."""
    profile = HardwareProfile.detect()
    assert isinstance(profile.gpu_available, bool)
    assert profile.gpu_name is None or isinstance(profile.gpu_name, str)
    assert isinstance(profile.gpu_memory_gb, float)
    assert isinstance(profile.cpu_count, int)
    assert isinstance(profile.ram_total_gb, float)
    assert profile.platform in ("win32", "linux", "darwin")
    assert isinstance(profile.python_version, str)
    assert profile.python_version.startswith(str(sys.version_info.major))


def test_hardware_profile_can_run_model():
    """Test the can_run_model method with various inputs."""
    profile = HardwareProfile.detect()
    # Should be able to run a tiny model
    assert profile.can_run_model(0.1, 32) is True
    # Should be unable to run an impossibly large model
    assert profile.can_run_model(100000, 32) is False
    # Quantization should help
    assert profile.can_run_model(10, 8) is True  # 10GB model at 8-bit -> 2.5GB effective
    assert profile.can_run_model(10, 64) is False  # 10GB at 64-bit -> 20GB effective


def test_brain_config_validation():
    """Test BrainConfig validation."""
    # Valid config
    config = BrainConfig(model_name="test", model_size_gb=1.0, quantization_bits=32)
    assert config.model_name == "test"
    assert config.model_size_gb == 1.0
    assert config.quantization_bits == 32

    # Invalid quantization bits
    with pytest.raises(ValidationError):
        BrainConfig(model_name="test", model_size_gb=1.0, quantization_bits=24)

    # Invalid device preference
    with pytest.raises(ValidationError):
        BrainConfig(model_name="test", model_size_gb=1.0, quantization_bits=32, device_preference="invalid")


def test_brain_response_immutable():
    """Test that BrainResponse is immutable (frozen)."""
    response = BrainResponse(content="test", confidence=0.9, latency_ms=10.0)
    assert response.content == "test"
    assert response.confidence == 0.9
    assert response.latency_ms == 10.0
    # Attempt to modify should raise an exception
    with pytest.raises(Exception):
        response.content = "modified"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])