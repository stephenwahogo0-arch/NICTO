import pytest
from ..reasoning.planner import Planner


def test_decompose():
    p = Planner()
    plan = p.decompose("Solve math problem 2+2", max_depth=2)
    assert isinstance(plan, dict) or hasattr(plan, "keys")


def test_plan_feasibility():
    p = Planner()
    plan = {"steps": [{"id": "s1"}, {"id": "s2"}]}
    score = p.evaluate_plan_feasibility(plan)
    assert 0.0 <= score <= 1.0


def test_subgoals():
    p = Planner()
    plan = {"steps": [{"id": "s1", "deps": []}, {"id": "s2", "deps": ["s1"]}]}
    subgoals = p.extract_subgoals(plan)
    assert isinstance(subgoals, list)


def test_reflection_engine():
    from ..reasoning.reflection import ReflectionEngine
    re = ReflectionEngine()
    task = {"input": "2+2", "domain": "math"}
    result = {"output": "4", "correct": True, "confidence": 0.9}
    ref = re.reflect(task, result)
    assert isinstance(ref, dict) or ref is None or len(ref) > 0