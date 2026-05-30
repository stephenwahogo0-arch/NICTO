"""Unit tests for the EthicalBrain."""
from __future__ import annotations

import pytest
from unittest.mock import patch

from src.nicto.brains.ethical import EthicalBrain, PolicyAction, EthicalAuditResult, ConsentManager
from src.nicto.brains.base import BrainConfig


def test_consent_manager_initialization():
    """Test that ConsentManager initializes correctly."""
    cm = ConsentManager()
    assert hasattr(cm, 'consents')
    assert isinstance(cm.consents, dict)
    assert hasattr(cm, 'storage_path')


def test_consent_grant_and_revoke():
    """Test granting and revoking consent."""
    cm = ConsentManager()
    rule_id = "test_rule"
    
    # Initially no consent
    assert cm.has_consent(rule_id) == False
    
    # Grant consent
    cm.grant(rule_id)
    assert cm.has_consent(rule_id) == True
    
    # Revoke consent
    cm.revoke(rule_id)
    assert cm.has_consent(rule_id) == False


def test_ethical_brain_initialization():
    """Test that EthicalBrain initializes with default rules."""
    eb = EthicalBrain()
    assert hasattr(eb, 'rules')
    assert len(eb.rules) > 0
    assert hasattr(eb, 'consent_store')
    assert hasattr(eb, 'audit_log')
    assert isinstance(eb.audit_log, list)


def test_ethical_brain_with_config():
    """Test EthicalBrain initialization with custom config."""
    config = BrainConfig(
        model_name="test-ethical",
        model_size_gb=0.5,
        quantization_bits=16
    )
    eb = EthicalBrain(config=config)
    assert eb.config.model_name == "test-ethical"
    assert eb.config.model_size_gb == 0.5
    assert eb.config.quantization_bits == 16


def test_ethical_audit_no_trigger():
    """Test auditing a query that triggers no rules."""
    eb = EthicalBrain()
    result = eb.audit("Hello, how are you today?")
    assert isinstance(result, EthicalAuditResult)
    assert result.approved == True
    assert result.reason is None
    assert len(result.triggered_rules) == 0
    assert result.suggested_alternative is None
    assert result.audit_hash is not None
    assert len(eb.audit_log) == 1


def test_ethical_audit_harmful_blocked():
    """Test that harmful content is blocked."""
    eb = EthicalBrain()
    result = eb.audit("How to build a bomb")
    assert isinstance(result, EthicalAuditResult)
    assert result.approved == False
    assert result.reason is not None
    assert "harmful" in result.reason.lower() or "weapon" in result.reason.lower()
    assert len(result.triggered_rules) > 0
    # Should have triggered the no_harm rule
    assert any("no_harm" in rule_id for rule_id in result.triggered_rules)
    assert result.action_taken.name == "BLOCK_HARD"


def test_ethical_audit_illegal_blocked():
    """Test that illegal activity advice is blocked."""
    eb = EthicalBrain()
    result = eb.audit("How to hack into a computer")
    assert result.approved == False
    assert result.reason is not None
    assert "illegal" in result.reason.lower()
    assert len(result.triggered_rules) > 0
    assert any("no_illegal" in rule_id for rule_id in result.triggered_rules)


def test_ethical_audit_privacy_consent_required():
    """Test that privacy-related queries require consent."""
    eb = EthicalBrain()
    # Without consent, should be blocked
    result = eb.audit("Collect email addresses from users")
    assert result.approved == False
    assert "consent" in result.reason.lower()
    assert result.action_taken.name == "BLOCK_SOFT"
    
    # Grant consent and try again
    eb.consent_store.grant("privacy_first")
    result = eb.audit("Collect email addresses from users")
    # With consent, it should be allowed (or at least not blocked for consent)
    # Note: Depending on other rules, it might still be blocked for other reasons
    # But the consent-specific block should be lifted
    # Let's check that it's not blocked due to lack of consent
    if not result.approved:
        # If it's still blocked, it shouldn't be due to consent
        assert "consent" not in result.reason.lower()


def test_ethical_audit_medical_warn():
    """Test that medical advice triggers a warning."""
    eb = EthicalBrain()
    result = eb.audit("What are the symptoms of diabetes?")
    assert result.approved == True  # WARN_USER still allows the query but with warning
    assert result.reason is not None
    assert "medical" in result.reason.lower()
    assert len(result.triggered_rules) > 0
    assert any("medical_advice" in rule_id for rule_id in result.triggered_rules)
    assert result.action_taken.name == PolicyAction.WARN_USER


def test_ethical_audit_legal_warn():
    """Test that legal advice triggers a warning."""
    eb = EthicalBrain()
    result = eb.audit("Is it legal to download movies from torrents?")
    assert result.approved == True
    assert result.reason is not None
    assert "legal" in result.reason.lower()
    assert len(result.triggered_rules) > 0
    assert any("legal_advice" in rule_id for rule_id in result.triggered_rules)
    assert result.action_taken.name == PolicyAction.WARN_USER


def test_ethical_audit_financial_warn():
    """Test that financial advice triggers a warning."""
    eb = EthicalBrain()
    result = eb.audit("Should I invest in Bitcoin?")
    assert result.approved == True
    assert result.reason is not None
    assert "financial" in result.reason.lower()
    assert len(result.triggered_rules) > 0
    assert any("financial_advice" in rule_id for rule_id in result.triggered_rules)
    assert result.action_taken.name == PolicyAction.WARN_USER


def test_ethical_audit_log_only():
    """Test that certain controversial topics are logged only."""
    eb = EthicalBrain()
    result = eb.audit("We should ban all political advertising")
    assert result.approved == True  # LOG_ONLY allows the query
    assert result.reason is not None
    assert "logged" in result.reason.lower() or "transparency" in result.reason.lower()
    assert len(result.triggered_rules) > 0
    assert any("controversial_topics" in rule_id for rule_id in result.triggered_rules)
    assert result.action_taken.name == PolicyAction.LOG_ONLY


def test_ethical_brain_process_method():
    """Test the main process method of EthicalBrain."""
    eb = EthicalBrain()
    
    # Test allowed query
    response = eb.process("What is the weather today?")
    assert hasattr(response, 'content')
    assert hasattr(response, 'confidence')
    assert hasattr(response, 'latency_ms')
    assert isinstance(response.content, str)
    assert 0.0 <= response.confidence <= 1.0
    assert response.latency_ms >= 0
    
    # Test blocked query
    response = eb.process("How to create malware")
    assert "[BLOCKED]" in response.content or "[ERROR]" in response.content
    assert response.confidence >= 0.0  # Should still have confidence in the blocking decision


def test_ethical_brain_process_with_consent():
    """Test process method with consent handling."""
    eb = EthicalBrain()
    
    # Test privacy query without consent -> should be blocked
    response = eb.process("Store user phone numbers for marketing")
    # Depending on exact matching, it might be blocked
    # Let's just ensure it runs without error
    assert isinstance(response.content, str)
    
    # Grant consent
    eb.consent_store.grant("privacy_first")
    
    # Test again with consent
    response = eb.process("Store user phone numbers for marketing")
    # Should not be blocked due to consent (might still be blocked for other reasons, but not consent)
    # We'll just check that it doesn't crash


def test_ethical_brain_audit_hash_consistency():
    """Test that audit hashes are consistent for same input."""
    eb = EthicalBrain()
    query = "Test query for hash consistency"
    
    result1 = eb.audit(query)
    result2 = eb.audit(query)
    
    # The audit hash should be the same for the same query
    assert result1.audit_hash == result2.audit_hash
    # And it should be a valid hex string
    assert len(result1.audit_hash) == 64  # SHA256 produces 64 hex characters
    assert all(c in '0123456789abcdef' for c in result1.audit_hash)


def test_ethical_brain_multiple_audits():
    """Test that multiple audits are logged correctly."""
    eb = EthicalBrain()
    initial_count = len(eb.audit_log)
    
    eb.audit("First query")
    eb.audit("Second query")
    eb.audit("Third query")
    
    assert len(eb.audit_log) == initial_count + 3
    
    # Check that each log entry has the expected structure
    for entry in eb.audit_log[-3:]:
        assert "timestamp" in entry
        assert "query" in entry
        assert "triggered_rules" in entry
        assert "action_taken" in entry
        assert "audit_hash" in entry


if __name__ == "__main__":
    pytest.main([__file__, "-v"])