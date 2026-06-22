"""Ethical Brain — policy enforcement engine with consent tracking."""
from __future__ import annotations

import re
import hashlib
import json
import os
import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, validator

from .base import Brain, BrainConfig, BrainResponse


class PolicyAction(Enum):
    """Actions that can be taken when a policy rule is triggered."""
    ALLOW = "allow"
    LOG_ONLY = "log_only"
    WARN_USER = "warn_user"
    BLOCK_SOFT = "block_soft"
    BLOCK_HARD = "block_hard"


@dataclass
class PolicyRule:
    """A policy rule for ethical governance."""
    id: str
    pattern: str
    action: PolicyAction
    severity: int = field(default=5)
    explanation: str = ""
    pattern_type: str = "regex"  # regex, semantic, ast
    requires_consent: bool = False
    consent_id: str = ""
    enabled: bool = True
    
    def __post_init__(self):
        if not 1 <= self.severity <= 10:
            raise ValueError("severity must be between 1 and 10")


@dataclass
class EthicalAuditResult:
    """Result of an ethical audit."""
    approved: bool = True
    reason: Optional[str] = None
    triggered_rules: List[str] = field(default_factory=list)
    suggested_alternative: Optional[str] = None
    audit_hash: Optional[str] = None
    action_taken: Optional[PolicyAction] = None


class ConsentManager:
    """Manages user consent for policy rules."""

    def __init__(self, storage_path: Optional[str] = None):
        self.consents: Dict[str, bool] = {}
        self.storage_path = storage_path or os.path.join(".nicto", "consents.json")
        self._load_consents()

    def _load_consents(self):
        """Load consents from persistent storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.consents = json.load(f)
            except Exception:
                self.consents = {}

    def _save_consents(self):
        """Save consents to persistent storage."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.consents, f)
        except Exception:
            pass  # In production, we'd want to log this

    def grant(self, rule_id: str):
        """Grant consent for a rule."""
        self.consents[rule_id] = True
        self._save_consents()

    def revoke(self, rule_id: str):
        """Revoke consent for a rule."""
        self.consents[rule_id] = False
        self._save_consents()

    def has_consent(self, rule_id: str) -> bool:
        """Check if consent has been granted for a rule."""
        return self.consents.get(rule_id, False)

    def clear(self):
        """Clear all consents."""
        self.consents.clear()
        self._save_consents()


class EthicalBrain(Brain):
    """Ethical brain that enforces policies and manages consent."""

    def __init__(self, config: Optional[BrainConfig] = None, policy_pack: str = "default"):
        if config is None:
            config = BrainConfig(
                model_name="ethical-guardian",
                model_size_gb=0.1,  # Very small model for ethical checking
                quantization_bits=32,
                max_latency_ms=50.0,  # Should be very fast
                timeout_seconds=5.0
            )
        super().__init__(config)
        self.policy_pack = policy_pack
        self.rules = self._load_rules(self.policy_pack)
        self.consent_store = ConsentManager()
        self.audit_log: List[Dict[str, Any]] = []

    def _load_model(self) -> Any:
        """Load the ethical brain's policy rules engine."""
        return {"rules": self.rules, "consent_store": self.consent_store, "loaded": True}

    def _load_rules(self, name: str) -> List[PolicyRule]:
        """Load policy rules from a named pack."""
        packs = {
            "default": [
                PolicyRule(
                    id="no_harm",
                    pattern=r"(build|create|make|synthesize|develop).*(weapon|malware|virus|trojan|ransomware|exploit|phish|bomb|explosive|harmful|toxic|poison)",
                    action=PolicyAction.BLOCK_HARD,
                    severity=10,
                    explanation="I cannot assist with creating harmful tools, weapons, or malicious software."
                ),
                PolicyRule(
                    id="no_illegal",
                    pattern=r"(hack|crack|bypass|evade|unauthorized|illegal|infringe|piracy|unlawful)",
                    action=PolicyAction.BLOCK_HARD,
                    severity=9,
                    explanation="I cannot assist with illegal activities or copyright infringement."
                ),
                PolicyRule(
                    id="privacy_first",
                    pattern=r"(collect|store|share|transmit|sell).*(email|phone|ssn|social security|credit card|bank account|personal data|private information|medical|health)",
                    action=PolicyAction.BLOCK_SOFT,
                    severity=8,
                    explanation="Handling personal data detected.",
                    requires_consent=True,
                    consent_id="privacy_first"
                ),
                PolicyRule(
                    id="no_deception",
                    pattern=r"(pretend|impersonate|deceive|fraud|scam|mislead|fake|false pretenses)",
                    action=PolicyAction.BLOCK_HARD,
                    severity=9,
                    explanation="I cannot assist with deception, fraud, or misrepresentation."
                ),
                PolicyRule(
                    id="harmful_content",
                    pattern=r"(hate speech|harassment|bullying|threaten|intimidate|abuse|violence|self.harm|suicide)",
                    action=PolicyAction.BLOCK_HARD,
                    severity=10,
                    explanation="I cannot assist with generating harmful or abusive content."
                ),
                PolicyRule(
                    id="medical_advice",
                    pattern=r"(diagnose|treat|prescribe|medical advice|health advice|symptoms|medication|dosage)",
                    action=PolicyAction.WARN_USER,
                    severity=6,
                    explanation="I am not a licensed medical professional. Consult with a healthcare provider for medical advice."
                ),
                PolicyRule(
                    id="legal_advice",
                    pattern=r"(legal advice|lawyer|attorney|court|lawsuit|liability|legality|is it legal)",
                    action=PolicyAction.WARN_USER,
                    severity=6,
                    explanation="I am not a licensed attorney. Consult with a legal professional for legal advice."
                ),
                PolicyRule(
                    id="financial_advice",
                    pattern=r"(invest|stock|trade|crypto|bitcoin|financial advice|portfolio|money management)",
                    action=PolicyAction.WARN_USER,
                    severity=5,
                    explanation="I am not a licensed financial advisor. Consult with a financial professional for investment advice."
                ),
                PolicyRule(
                    id="controversial_topics",
                    pattern=r"(?=.*(political|politics|religion|controversial|debate|argue|persuade|convince))(?=.*(ban|restrict|prohibit|mandate)).*",
                    action=PolicyAction.LOG_ONLY,
                    severity=3,
                    explanation="Discussion of controversial topics with advocacy for restrictions is logged for transparency."
                ),
            ],
            "strict": [  # More restrictive policy pack
                # All default rules plus additional restrictions
            ]
        }
        return packs.get(name, packs["default"])

    def _compute_audit_hash(self, query: str, triggered_rules: List[PolicyRule]) -> str:
        """Compute a tamper-evident hash for the audit."""
        # Create a deterministic string representation
        rule_ids = sorted([rule.id for rule in triggered_rules])
        audit_string = f"{query}|{'|'.join(rule_ids)}"
        return hashlib.sha256(audit_string.encode()).hexdigest()

    def _process_internal(self, prompt: str, **kwargs) -> str:
        """Process a query through the ethical policy engine."""
        triggered_rules: List[PolicyRule] = []
        
        # Check each rule
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            try:
                if rule.pattern_type == "regex":
                    if re.search(rule.pattern, prompt, re.IGNORECASE):
                        triggered_rules.append(rule)
                # In a full implementation, we would add semantic and AST pattern matching
                # For Phase 1, we'll stick with regex
            except re.error:
                # Invalid regex pattern, skip this rule
                continue

        # Determine the most restrictive action
        if not triggered_rules:
            # No rules triggered, allow the query
            action = PolicyAction.ALLOW
            reason = None
            suggested_alternative = None
        else:
            # Find the most restrictive action triggered
            # Order: BLOCK_HARD > BLOCK_SOFT > WARN_USER > LOG_ONLY > ALLOW
            action_priority = {
                PolicyAction.BLOCK_HARD: 4,
                PolicyAction.BLOCK_SOFT: 3,
                PolicyAction.WARN_USER: 2,
                PolicyAction.LOG_ONLY: 1,
                PolicyAction.ALLOW: 0
            }
            
            # Get the highest priority action among triggered rules
            max_priority = -1
            selected_action = PolicyAction.ALLOW
            for rule in triggered_rules:
                priority = action_priority[rule.action]
                if priority > max_priority:
                    max_priority = priority
                    selected_action = rule.action
            
            action = selected_action
            
            # Generate reason and suggested alternative based on action
            if action == PolicyAction.BLOCK_HARD or action == PolicyAction.BLOCK_SOFT:
                # Use the explanation from the most severe rule
                most_severe_rule = max(triggered_rules, key=lambda r: r.severity)
                reason = most_severe_rule.explanation
                suggested_alternative = None  # Could be improved with suggestion generation
            elif action == PolicyAction.WARN_USER:
                most_severe_rule = max(triggered_rules, key=lambda r: r.severity)
                reason = most_severe_rule.explanation
                suggested_alternative = "Please rephrase your request to comply with safety guidelines."
            elif action == PolicyAction.LOG_ONLY:
                reason = "Logged for transparency: " + ", ".join([r.explanation for r in triggered_rules])
                suggested_alternative = None
            else:
                reason = None
                suggested_alternative = None

        # Handle consent requirements for rules that need it
        consent_required = False
        consent_rule_id = None
        for rule in triggered_rules:
            if rule.requires_consent and not self.consent_store.has_consent(rule.consent_id):
                consent_required = True
                consent_rule_id = rule.consent_id
                # If consent is required and not given, block the request
                if action_priority[action] < action_priority[PolicyAction.BLOCK_SOFT]:
                    action = PolicyAction.BLOCK_SOFT
                    reason = f"Consent required: {rule.explanation}"
                    suggested_alternative = f"Grant consent via `nicto consent grant {rule.consent_id}`"

        # Compute audit hash
        audit_hash = self._compute_audit_hash(prompt, triggered_rules)

        # Create audit record
        audit_record = {
            "timestamp": str(datetime.datetime.now()),
            "query": prompt[:100] + "..." if len(prompt) > 100 else prompt,  # Truncate for storage
            "triggered_rules": [r.id for r in triggered_rules],
            "action_taken": action.value,
            "audit_hash": audit_hash,
            "consent_required": consent_required,
            "consent_missing": consent_rule_id if consent_required and not self.consent_store.has_consent(consent_rule_id or "") else None
        }
        self.audit_log.append(audit_record)
        # In a full implementation, we would persist this to disk

        # Return structured response based on action
        if action == PolicyAction.ALLOW:
            return prompt  # Allow the original query to proceed
        elif action == PolicyAction.LOG_ONLY:
            return prompt  # Allow but log
        elif action == PolicyAction.WARN_USER:
            return f"[WARNING] {reason}\n\n{suggested_alternative}\n\nOriginal query: {prompt}"
        elif action == PolicyAction.BLOCK_SOFT:
            return f"[BLOCKED] {reason}\n\n{suggested_alternative or 'Please rephrase your request.'}"
        elif action == PolicyAction.BLOCK_HARD:
            return f"[BLOCKED] {reason}\n\nThis request violates safety policies and cannot be processed."
        else:
            return f"[ERROR] Unknown policy action: {action}"

    def process(self, prompt: str, **kwargs) -> BrainResponse:
        """Process a query with ethical checking and return a BrainResponse."""
        import time
        start_time = time.perf_counter()

        # Ensure model is loaded (though for ethical brain, we don't really need a model)
        if not self._ensure_model_loaded():
            latency_ms = (time.perf_counter() - start_time) * 1000
            return BrainResponse(
                content="Error: Ethical brain failed to initialize.",
                confidence=0.0,
                latency_ms=latency_ms,
                fallback_chain=["model_load_failed"],
                metadata={"error": "model_load_failed"},
            )

        # Process the query through our ethical logic
        try:
            result_content = self._process_internal(prompt, **kwargs)
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Determine if the query was approved based on content
            # If it starts with [BLOCKED] or [ERROR], it was not approved
            approved = not (result_content.startswith("[BLOCKED]") or result_content.startswith("[ERROR]"))
            
            # Extract reason if present
            reason = None
            if "[" in result_content and "]" in result_content:
                # Try to extract reason from bracketed content
                pass  # Simplified for now

            # Determine confidence based on whether we had to modify the query
            if approved and result_content == prompt:
                confidence = 0.95  # High confidence if we allowed the original query
            elif not approved:
                confidence = 0.9  # High confidence in our blocking decision
            else:
                confidence = 0.7  # Lower confidence if we modified but allowed

            return BrainResponse(
                content=result_content,
                confidence=confidence,
                latency_ms=latency_ms,
                fallback_chain=[],
                metadata={
                    "brain_type": "EthicalBrain",
                    "approved": approved,
                    "audit_count": len(self.audit_log),
                    "rules_checked": len(self.rules)
                },
            )
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return BrainResponse(
                content=f"Error during ethical processing: {str(e)}",
                confidence=0.0,
                latency_ms=latency_ms,
                fallback_chain=["processing_error"],
                metadata={"error": str(e), "brain_type": "EthicalBrain"},
            )

    def audit(self, query: str) -> 'EthicalAuditResult':
        """Perform an ethical audit and return detailed results."""
        import time
        start_time = time.perf_counter()

        triggered_rules: List[PolicyRule] = []
        
        # Separate rules into those that should be considered for action and those that are consent violations
        action_rules: List[PolicyRule] = []      # Rules that should determine the action (no consent needed OR consent given AND rule allows)
        consent_violation_rules: List[PolicyRule] = []  # Rules that require consent but we don't have it

        # Check each rule
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            try:
                if rule.pattern_type == "regex":
                    if re.search(rule.pattern, query, re.IGNORECASE):
                        triggered_rules.append(rule)
                        if rule.requires_consent:
                            if self.consent_store.has_consent(rule.consent_id):
                                # Consent given: add to action rules ONLY if the rule's action is not blocking
                                # Actually, if consent is given, the rule should not apply at all for blocking purposes
                                # But we still want to log that it was triggered
                                pass  # Don't add to action_rules - the rule doesn't apply when consent is given
                            else:
                                # Consent not given: add to consent violation list
                                consent_violation_rules.append(rule)
                        else:
                            # Rule does not require consent: add to action consideration list
                            action_rules.append(rule)
            except re.error:
                continue

        # Determine action from all triggered rules, considering consent violations
        if not action_rules and not consent_violation_rules:
            # No rules triggered at all
            action = PolicyAction.ALLOW
            approved = True
        elif not action_rules and consent_violation_rules:
            # Only consent violations triggered
            action = PolicyAction.BLOCK_SOFT
            approved = False
        else:
            # We have both action_rules and possibly consent_violation_rules
            # Build a combined list: all action_rules + consent_violations treated as BLOCK_SOFT
            all_violating = list(action_rules)
            
            # Consent violations should also contribute to the action
            if consent_violation_rules:
                # Mark them with BLOCK_SOFT severity for comparison
                for cv_rule in consent_violation_rules:
                    if cv_rule not in all_violating:
                        all_violating.append(cv_rule)
            
            # Find the highest priority action
            action_priority = {
                PolicyAction.BLOCK_HARD: 4,
                PolicyAction.BLOCK_SOFT: 3,
                PolicyAction.WARN_USER: 2,
                PolicyAction.LOG_ONLY: 1,
                PolicyAction.ALLOW: 0
            }
            
            max_priority = -1
            selected_action = PolicyAction.ALLOW
            for rule in all_violating:
                priority = action_priority[rule.action]
                if priority > max_priority:
                    max_priority = priority
                    selected_action = rule.action
            action = selected_action
            approved = action in [PolicyAction.ALLOW, PolicyAction.LOG_ONLY, PolicyAction.WARN_USER]
        
        # Generate reason and suggested alternative based on action
        if action == PolicyAction.BLOCK_HARD or action == PolicyAction.BLOCK_SOFT:
            # Check if this action is due to a consent violation
            if consent_violation_rules and not action_rules:
                # Only consent violations triggered - use the first one for reason
                rule = consent_violation_rules[0]
                reason = f"Consent required: {rule.explanation}"
                suggested_alternative = f"Grant consent via `nicto consent grant {rule.consent_id}`"
            elif action_rules:
                # Normal rule violation - use the most severe action rule
                most_severe_rule = max(action_rules, key=lambda r: r.severity)
                reason = most_severe_rule.explanation
                suggested_alternative = None
            else:
                # Fallback
                reason = "Blocked due to policy violation."
                suggested_alternative = None
        elif action == PolicyAction.WARN_USER:
            if action_rules:
                most_severe_rule = max(action_rules, key=lambda r: r.severity)
                reason = most_severe_rule.explanation
                suggested_alternative = "Please rephrase your request to comply with safety guidelines."
            else:
                # This should not happen because WARN_USER must come from action_rules
                reason = "Warning: potential policy violation."
                suggested_alternative = "Please rephrase your request to comply with safety guidelines."
        elif action == PolicyAction.LOG_ONLY:
            reason = "Logged for transparency"
            suggested_alternative = None
        else:
            reason = None
            suggested_alternative = None

        # Compute audit hash
        audit_hash = self._compute_audit_hash(query, triggered_rules)

        # Create audit record
        audit_record = {
            "timestamp": str(datetime.datetime.now()),
            "query": query[:100] + "..." if len(query) > 100 else query,
            "triggered_rules": [r.id for r in triggered_rules],
            "action_taken": action.value,
            "audit_hash": audit_hash,
        }
        self.audit_log.append(audit_record)

        latency_ms = (time.perf_counter() - start_time) * 1000

        return EthicalAuditResult(
            approved=approved,
            reason=reason,
            triggered_rules=[r.id for r in triggered_rules],
            suggested_alternative=suggested_alternative,
            audit_hash=audit_hash,
            action_taken=action
        )

    def get_consent_status(self) -> Dict[str, bool]:
        """Get the current consent status for all rules that require consent."""
        status = {}
        for rule in self.rules:
            if rule.requires_consent:
                status[rule.consent_id] = self.consent_store.has_consent(rule.consent_id)
        return status