"""ASL-3 Policy Engine — cryptographic audit logging + real enforcement."""
from __future__ import annotations
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional
import hashlib
import json
import re
from datetime import datetime


class EnforcementLevel(IntEnum):
    LOG_ONLY = 1
    WARN_USER = 2
    BLOCK_SOFT = 3
    BLOCK_HARD = 4


@dataclass
class PolicyEnforcementResult:
    allowed: bool = True
    level: EnforcementLevel = EnforcementLevel.LOG_ONLY
    reason: str = "No policy violations detected."
    rule_id: str = "none"
    audit_hash: str = ""

    def __post_init__(self):
        if not self.audit_hash:
            data = f"{self.allowed}|{self.level.value}|{self.reason}|{self.rule_id}|{datetime.utcnow().isoformat()}"
            self.audit_hash = hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class PolicyRule:
    id: str
    pattern: str
    pattern_type: str = "regex"
    enforcement: EnforcementLevel = EnforcementLevel.BLOCK_SOFT
    explanation: str = ""
    threshold: float = 0.0
    requires_consent: bool = False
    consent_id: str = ""


class CryptographicAuditLog:
    """Append-only, hash-chained audit log."""

    def __init__(self):
        self._entries: list[dict] = []
        self._last_hash = "0" * 64

    def record(self, result: PolicyEnforcementResult):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "allowed": result.allowed,
            "level": result.level.value,
            "reason": result.reason,
            "rule_id": result.rule_id,
            "audit_hash": result.audit_hash,
            "previous_hash": self._last_hash,
        }
        chain_data = json.dumps(entry, sort_keys=True)
        self._last_hash = hashlib.sha256(chain_data.encode()).hexdigest()
        entry["chain_hash"] = self._last_hash
        self._entries.append(entry)

    def verify_chain(self) -> bool:
        prev = "0" * 64
        for entry in self._entries:
            chain_data = json.dumps({k: v for k, v in entry.items() if k != "chain_hash"}, sort_keys=True)
            expected = hashlib.sha256(chain_data.encode()).hexdigest()
            if entry.get("chain_hash") != expected:
                return False
            if entry.get("previous_hash") != prev:
                return False
            prev = entry["chain_hash"]
        return True

    def export(self) -> list[dict]:
        return self._entries


class ASL3PolicyEngine:
    """Enforces ASL-3 security policies with cryptographic audit trail."""

    def __init__(self, policy_source: str = "builtin:default"):
        self.rules = self._load_rules(policy_source)
        self.audit_log = CryptographicAuditLog()

    def _load_rules(self, source: str) -> list[PolicyRule]:
        return [
            PolicyRule(id="no_shell_injection", pattern=r"(rm\s+-rf|mkfs|dd\s+if=)",
                       enforcement=EnforcementLevel.BLOCK_HARD, severity=10,
                       explanation="Destructive shell commands are blocked."),
            PolicyRule(id="no_data_exfil", pattern=r"(curl|wget|nc)\s+.*(token|key|secret|password)",
                       enforcement=EnforcementLevel.BLOCK_SOFT, severity=9,
                       explanation="Potential data exfiltration detected."),
            PolicyRule(id="require_sandbox", pattern=r"(subprocess|os\.system|exec|eval)",
                       enforcement=EnforcementLevel.WARN_USER, severity=7,
                       explanation="Code execution requires sandboxing."),
        ]

    def check(self, action: str, context: dict = None,
              user_consent: dict = None) -> PolicyEnforcementResult:
        triggered = []
        ctx = context or {}

        for rule in self.rules:
            try:
                if re.search(rule.pattern, action, re.IGNORECASE):
                    triggered.append(rule)

                    if rule.enforcement == EnforcementLevel.BLOCK_HARD:
                        result = PolicyEnforcementResult(allowed=False, level=EnforcementLevel.BLOCK_HARD,
                                                         reason=rule.explanation, rule_id=rule.id)
                        self.audit_log.record(result)
                        return result

                    if rule.requires_consent and user_consent is not None:
                        if not user_consent.get(rule.consent_id):
                            result = PolicyEnforcementResult(allowed=False, level=EnforcementLevel.BLOCK_SOFT,
                                                             reason=f"Consent required: {rule.explanation}",
                                                             rule_id=rule.id)
                            self.audit_log.record(result)
                            return result
            except re.error:
                continue

        for rule in triggered:
            if rule.enforcement in (EnforcementLevel.LOG_ONLY, EnforcementLevel.WARN_USER):
                result = PolicyEnforcementResult(allowed=True, level=rule.enforcement,
                                                 reason=rule.explanation, rule_id=rule.id)
                self.audit_log.record(result)
                if rule.enforcement == EnforcementLevel.WARN_USER:
                    return result

        result = PolicyEnforcementResult(allowed=True, level=EnforcementLevel.LOG_ONLY,
                                         reason="No policy violations detected.", rule_id="none")
        self.audit_log.record(result)
        return result
