import pytest
import numpy as np
from ..learning.reward_shaper import RewardShaper


def test_progress_bonus():
    rs = RewardShaper()
    bonus = rs.progress_bonus(0.8)
    assert bonus > 0.0


def test_creativity_bonus_gated():
    rs = RewardShaper()
    bonus = rs.creativity_bonus(0.8, quality_gate=0.7)
    assert bonus >= 0.0
    bonus_low = rs.creativity_bonus(0.8, quality_gate=0.9)
    assert bonus_low == 0.0


def test_anti_hacking():
    rs = RewardShaper()
    reward = rs.anti_hacking(10.0, 0.2)
    assert reward < 10.0


def test_bonus_gate():
    rs = RewardShaper()
    assert rs.bonus_gate(5.0, True) == 5.0
    assert rs.bonus_gate(5.0, False) == 0.0