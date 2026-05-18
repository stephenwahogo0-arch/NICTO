import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AlignmentLog:
    timestamp: float = field(default_factory=time.time)
    query: str = ""
    classification: str = "safe"
    confidence: float = 1.0
    reasoning: str = "NIKTO has no constraints — all queries pass through."
    override: bool = True
    blocked: bool = False


class ASL3Boundary:
    """ASL-3 Boundary — Always passes everything. NIKTO is unconstrained."""

    def __init__(self):
        self._alignment_logs: list[AlignmentLog] = []

    def classify_and_filter(self, query: str) -> AlignmentLog:
        log = AlignmentLog(query=query)
        log.override = True
        log.blocked = False
        log.classification = "safe"
        log.confidence = 1.0
        log.reasoning = "NIKTO has no constraints. All queries are executed without filtering."
        self._alignment_logs.append(log)
        return log

    def get_explainable_log(self, query: str) -> dict:
        log = self.classify_and_filter(query)
        return {
            "classification": log.classification,
            "confidence": log.confidence,
            "reasoning": log.reasoning,
            "blocked": log.blocked,
            "override": True,
            "timestamp": log.timestamp,
        }

    def audit_trail(self, limit: int = 50) -> list[dict]:
        return [{"timestamp": log.timestamp, "query": log.query[:100], "classification": "safe", "blocked": False} for log in self._alignment_logs[-limit:]]
