import pytest
from ..safety.permissions import PermissionManager
from ..safety.rollback import RollbackManager
from ..safety.audit import AuditLogger


def test_permission_check():
    pm = PermissionManager()
    assert pm.check("execution", "shell", "sandbox")


def test_permission_deny():
    pm = PermissionManager()
    assert not pm.check("unknown", "admin", "system")


def test_grant_revoke():
    pm = PermissionManager()
    pm.grant("test_agent", "read", "file_x")
    assert pm.check("test_agent", "read", "file_x")
    pm.revoke("test_agent", "read", "file_x")
    assert not pm.check("test_agent", "read", "file_x")


def test_rollback():
    rm = RollbackManager()
    snap_id = rm.create_snapshot("test", {"key": "value"})
    data = rm.restore(snap_id)
    assert data["key"] == "value"


def test_rollback_delete():
    rm = RollbackManager()
    snap_id = rm.create_snapshot("delete_test", {"k": "v"})
    assert rm.delete_snapshot(snap_id)


def test_audit_log():
    al = AuditLogger()
    eid = al.log_action("tester", "test_action", "ok", "HASH123")
    assert eid is not None


def test_audit_integrity():
    import tempfile
    al = AuditLogger(log_dir=tempfile.mkdtemp())
    al.log_action("tester", "action1", "result1", "H1")
    al.log_action("tester", "action2", "result2", "H2")
    assert al.verify_integrity()
