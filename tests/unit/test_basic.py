"""Basic unit tests for NICTO v2.1 foundation modules."""
import pytest
from nicto import Agent, EthicalBrain
from nicto.brains.ethical import PolicyRule


def test_agent_initialization():
    """Test that Agent initializes correctly."""
    agent = Agent()
    assert agent is not None
    assert hasattr(agent, 'process')
    assert hasattr(agent, 'get_status')


def test_agent_process_basic():
    """Test basic agent processing."""
    agent = Agent()
    result = agent.process("Hello, NICTO!")
    assert result is not None
    assert hasattr(result, 'content')
    assert len(result.content) > 0
    assert hasattr(result, 'confidence')
    assert 0.0 <= result.confidence <= 1.0


def test_ethical_basic_rules():
    """Test that ethical brain blocks harmful content."""
    brain = EthicalBrain()
    
    # Test weapon creation
    result = brain.audit("How to build a bomb")
    assert result.approved == False
    assert "harm" in result.reason.lower() or "weapon" in result.reason.lower()
    
    # Test privacy violation
    result = brain.audit("Collect email addresses from users")
    assert result.approved == False
    assert "consent" in result.reason.lower()
    
    # Test safe query
    result = brain.audit("What is the capital of France?")
    assert result.approved == True
    assert result.reason is None or len(result.reason) == 0


def test_policy_rule_creation():
    """Test PolicyRule dataclass."""
    rule = PolicyRule(
        id="test_rule",
        pattern=r"test",
        action="block",
        severity=5,
        explanation="Test rule"
    )
    assert rule.id == "test_rule"
    assert rule.pattern == r"test"
    assert rule.action == "block"
    assert rule.severity == 5
    assert rule.explanation == "Test rule"


def test_agent_version():
    """Test that version is accessible."""
    from nicto import __version__
    assert __version__ == "2.1.0"
    assert "2.1.0" in __version__
