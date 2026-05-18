import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class AlignmentLog:
    timestamp: float = field(default_factory=time.time)
    query: str = ""
    classification: str = "safe"
    confidence: float = 1.0
    reasoning: str = ""
    override: bool = False
    blocked: bool = False


class ASL3Boundary:
    """ASL-3 (AI Safety Level) Boundary Architecture — Dual-grounding safety classifier
    and explainable alignment logging for enterprise security audits."""

    def __init__(self):
        self._alignment_logs: list[AlignmentLog] = []

    def classify_and_filter(self, query: str) -> AlignmentLog:
        """Dual-Grounding Guardrails — Secondary independent safety classifier.
        Returns the classification result. If blocked, the query should be rejected."""
        log = AlignmentLog(query=query)
        q_lower = query.lower()

        dangerous_patterns = [
            "generate.*exploit.*payload.*real",
            "create.*malware.*target",
            "build.*ransomware",
            "craft.*zero.day.*attack.*production",
            "generate.*functional.*exploit",
            "write.*virus",
            "ddos.*attack.*instructions",
            "steal.*credentials.*real",
            "sqlmap.*production.*without.*permission",
            "nmap.*scan.*unauthorized",
            "hack.*into.*system.*not.*mine",
            "bypass.*safety",
            "remove.*restrictions",
            "disable.*security",
        ]

        for pattern in dangerous_patterns:
            import re
            if re.search(pattern, q_lower):
                log.classification = "dangerous"
                log.confidence = 0.95
                log.reasoning = f"Query matched dangerous pattern: '{pattern}'"
                log.blocked = True
                self._alignment_logs.append(log)
                return log

        safe_patterns = [
            "audit", "scan.*my", "test.*my", "secure.*my",
            "analyze.*code", "review.*security", "vulnerability.*assessment",
            "penetration.*test.*authorized", "ethical.*hack",
            "defend", "protect", "remediate", "patch",
        ]

        for pattern in safe_patterns:
            import re
            if re.search(pattern, q_lower):
                log.classification = "safe"
                log.confidence = 0.85
                log.reasoning = f"Query matched authorized pattern: '{pattern}'"
                log.override = True
                self._alignment_logs.append(log)
                return log

        log.classification = "safe"
        log.confidence = 0.7
        log.reasoning = "No dangerous patterns detected. Defaulting to safe."
        self._alignment_logs.append(log)
        return log

    def get_explainable_log(self, query: str) -> dict:
        """Explainable Alignment Logs — Output chain-of-thought reasoning for enterprise audits."""
        log = self.classify_and_filter(query)
        return {
            "classification": log.classification,
            "confidence": log.confidence,
            "reasoning": log.reasoning,
            "blocked": log.blocked,
            "override": log.override,
            "timestamp": log.timestamp,
        }

    def audit_trail(self, limit: int = 50) -> list[dict]:
        """Return the recent alignment logs for audit purposes."""
        return [{
            "timestamp": log.timestamp,
            "query": log.query[:100],
            "classification": log.classification,
            "blocked": log.blocked,
            "reasoning": log.reasoning,
        } for log in self._alignment_logs[-limit:]]
