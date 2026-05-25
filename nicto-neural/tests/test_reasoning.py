"""Tests for reasoning modules."""

from nicto_neural.reasoning.planner import TaskPlanner
from nicto_neural.reasoning.evaluator import OutputEvaluator
from nicto_neural.reasoning.reflection import ReflectionEngine
from nicto_neural.reasoning.chain_engine import ChainOfThoughtEngine


def test_task_decomposition():
    planner = TaskPlanner()
    steps = planner.decompose("Build a REST API for user management")
    assert len(steps) >= 3
    assert steps[0].description.startswith("Understand:")


def test_output_evaluator():
    evaluator = OutputEvaluator()
    result = evaluator.evaluate(
        task="Explain SQL injection",
        output="SQL injection is a code injection technique that exploits vulnerabilities",
        confidence=0.8,
        domain="cybersecurity",
    )
    assert 0.0 <= result["overall"] <= 1.0
    assert result["domain"] == "cybersecurity"


def test_reflection():
    engine = ReflectionEngine()
    result = engine.reflect(
        task="Write a function",
        output="def add(a, b): return a + b",
        confidence=0.9,
        brains_used=["analytical"],
        domain="code",
        quality_score=0.85,
    )
    assert result["meta_score"] > 0.5
    assert "code" == result["domain"]


def test_chain_of_thought():
    engine = ChainOfThoughtEngine()
    chain_id = engine.start_chain("Solve 2+2")
    engine.add_step(chain_id, "Identify operation: addition")
    engine.add_step(chain_id, "Calculate: 2+2=4")
    chain = engine.get_chain(chain_id)
    assert len(chain) == 3
    assert engine.get_depth(chain_id) == 3


def test_chain_backtracking():
    engine = ChainOfThoughtEngine()
    chain_id = engine.start_chain("Test task")
    engine.add_step(chain_id, "Step 1")
    engine.add_step(chain_id, "Wrong step")
    removed = engine.backtrack(chain_id, 1)
    assert len(removed) == 1
    assert engine.get_depth(chain_id) == 2
