"""Tests for ELO rating system."""

from nicto_neural.neural.config import NeuralConfig
from nicto_neural.neural.elo_system import EloSystem


def test_elo_update_correctness():
    elo = EloSystem(NeuralConfig())
    before = elo.get_rating("analytical", "math")
    elo.update("analytical", "math", 1.0)
    after = elo.get_rating("analytical", "math")
    assert after > before


def test_elo_decrease_on_loss():
    elo = EloSystem(NeuralConfig())
    before = elo.get_rating("analytical", "math")
    elo.update("analytical", "math", 0.0)
    after = elo.get_rating("analytical", "math")
    assert after < before


def test_elo_convergence():
    elo = EloSystem(NeuralConfig())
    for _ in range(50):
        elo.update("analytical", "math", 0.5)
    rating = elo.get_rating("analytical", "math")
    assert abs(rating - 1500.0) < 50.0


def test_per_domain_elo():
    elo = EloSystem(NeuralConfig())
    elo.update("analytical", "math", 1.0)
    math_rating = elo.get_rating("analytical", "math")
    code_rating = elo.get_rating("analytical", "code")
    assert math_rating > code_rating


def test_leaderboard():
    config = NeuralConfig()
    elo = EloSystem(config)
    elo.update("analytical", "math", 1.0)
    board = elo.get_leaderboard("math")
    assert len(board) == len(config.brain_names)
    assert board[0][0] == "analytical"
