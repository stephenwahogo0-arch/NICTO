"""Tests for safety system."""

from nicto_neural.safety.permissions import PermissionManager
from nicto_neural.safety.rollback import RollbackManager
from nicto_neural.safety.audit import AuditLogger
from nicto_neural.safety.policies import SafetyPolicies


def test_permissions_default():
    pm = PermissionManager()
    assert pm.check("read_memory") is True
    assert pm.check("deploy") is False


def test_permission_grant_revoke():
    pm = PermissionManager()
    pm.grant("deploy", reason="testing")
    assert pm.check("deploy") is True
    pm.revoke("deploy", reason="done testing")
    assert pm.check("deploy") is False


def test_rollback_snapshot():
    rm = RollbackManager()
    sid = rm.snapshot({"count": 42}, label="test")
    restored = rm.restore(sid)
    assert restored["count"] == 42


def test_audit_chain():
    audit = AuditLogger()
    audit.log("test_action", {"key": "value"})
    audit.log("another_action")
    result = audit.verify_chain()
    assert result["valid"] is True
    assert result["entries"] == 2


def test_rate_limiting():
    policies = SafetyPolicies()
    policies.set_rate_limit("test_op", max_calls=2, window_seconds=60.0)
    assert policies.check_rate_limit("test_op")["allowed"] is True
    assert policies.check_rate_limit("test_op")["allowed"] is True
    assert policies.check_rate_limit("test_op")["allowed"] is False


def test_recursion_guard():
    policies = SafetyPolicies()
    policies._max_recursion = 3
    assert policies.check_recursion("ctx1")["allowed"] is True
    assert policies.check_recursion("ctx1")["allowed"] is True
    assert policies.check_recursion("ctx1")["allowed"] is True
    assert policies.check_recursion("ctx1")["allowed"] is False
