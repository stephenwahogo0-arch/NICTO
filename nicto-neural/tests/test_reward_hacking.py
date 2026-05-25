"""Tests for reward hacking detection."""

from nicto_neural.safety.reward_hacking import RewardHackingDetector


def test_flat_quality_rising_reward_detected():
    detector = RewardHackingDetector()
    for i in range(5):
        result = detector.check(0, quality=0.5, reward=i * 0.5)
    assert result["hacking_detected"] is True


def test_action_repeat_detected():
    detector = RewardHackingDetector()
    for _ in range(6):
        result = detector.check(3, quality=0.8, reward=1.0)
    assert "action_3_repeated_5_times" in str(result["flags"])


def test_clean_session_no_flag():
    detector = RewardHackingDetector()
    result = detector.check(0, quality=0.9, reward=9.0)
    assert result["hacking_detected"] is False


def test_reward_increase_no_completion():
    detector = RewardHackingDetector()
    detector.check(0, quality=0.5, reward=1.0)
    result = detector.check(1, quality=0.5, reward=2.0, task_completed=False)
    assert "reward_increase_no_completion" in result["flags"]


def test_get_stats():
    detector = RewardHackingDetector()
    for i in range(10):
        detector.check(i % 3, quality=0.5 + i * 0.01, reward=float(i))
    stats = detector.get_stats()
    assert stats["total_checks"] == 10
