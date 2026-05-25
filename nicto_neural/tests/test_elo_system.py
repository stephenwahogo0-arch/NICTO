import pytest
from ..neural.elo_system import ELOEstimator


def test_elo_initialization():
    elo = ELOEstimator()
    assert elo.get_rating("primary", "general") == 1500.0


def test_elo_update():
    elo = ELOEstimator()
    update = elo.update("primary", "general", won=True, opponent_rating=1500.0)
    assert update.new_rating > update.old_rating


def test_elo_convergence():
    elo = ELOEstimator()
    for _ in range(20):
        elo.update("primary", "general", won=True, opponent_rating=1500.0)
    assert elo.get_rating("primary", "general") > 1520.0


def test_elo_loss():
    elo = ELOEstimator()
    update = elo.update("primary", "general", won=False, opponent_rating=2000.0)
    assert update.new_rating < update.old_rating


def test_best_brain():
    elo = ELOEstimator()
    elo.update("analytical", "code", won=True, opponent_rating=1500.0)
    elo.update("primary", "code", won=False, opponent_rating=1500.0)
    best, _ = elo.best_brain("code")
    assert best == "analytical"


def test_rankings():
    elo = ELOEstimator()
    elo.update("analytical", "code", won=True, opponent_rating=1500.0)
    elo.update("primary", "code", won=False, opponent_rating=1500.0)
    rankings = elo.brain_rankings("code")
    assert len(rankings) == 6
    assert rankings[0][0] == "analytical"