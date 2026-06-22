import pytest
from ..safety.reward_hacking import RewardHackingDetector


def test_detect_hacking():
    detector = RewardHackingDetector()
    rewards = [1.0] * 3 + [5.0, 8.0]
    qualities = [0.5] * 5
    detected, score = detector.detect(rewards, qualities)
    assert detected or score > 0.0


def test_no_hacking():
    detector = RewardHackingDetector()
    rewards = [1.0, 1.1, 1.0, 1.2, 1.1]
    qualities = [0.5, 0.6, 0.55, 0.7, 0.65]
    detected, score = detector.detect(rewards, qualities)
    assert not detected


def test_flag():
    detector = RewardHackingDetector()
    detector.flag_hacking("analytical", "Flat quality + rising reward")
    flags = detector.get_flags("analytical")
    assert len(flags) == 1


def test_clear():
    detector = RewardHackingDetector()
    detector.flag_hacking("analytical", "test")
    detector.clear_flags("analytical")
    assert len(detector.get_flags("analytical")) == 0