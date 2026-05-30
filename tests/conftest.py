"""Pytest configuration for NICTO test suite."""
import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def agent():
    """Fixture providing a basic NICTO agent."""
    from nicto import Agent
    return Agent()


@pytest.fixture
def ethical_brain():
    """Fixture providing an EthicalBrain instance."""
    from nicto.brains.ethical import EthicalBrain
    return EthicalBrain()


@pytest.fixture(autouse=True)
def enforce_determinism():
    """Ensure reproducible tests by seeding RNGs."""
    import torch
    import numpy as np
    import random
    import os
    
    # Seed all random number generators
    torch.manual_seed(42)
    np.random.seed(42)
    random.seed(42)
    os.environ["PYTHONHASHSEED"] = "42"
    
    # Make CUDA operations deterministic if available
    if torch.cuda.is_available():
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    
    yield
    
    # Reset seeds after test if needed