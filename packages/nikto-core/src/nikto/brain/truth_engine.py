"""NIKTO Truth Engine — Anti-hallucination, fact-checking, confidence tracking."""

import json
import math
import hashlib
import uuid
import re
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict


class FactRecord:
    def __init__(self, claim: str, confidence: float = 0.5, source: str = "unknown",
                 category: str = "general", evidence: list = None,
                 contradictions: list = None, tags: list = None):
        self.id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]
        self.claim = claim
        self.confidence = max(0.0, min(1.0, confidence))
        self.source = source
        self.category = category
        self.evidence = evidence or []
        self.contradictions = contradictions or []
        self.tags = tags or []
        self.verified = False
        self.verification_level = None
        self.created = datetime.now(timezone.utc).isoformat()
        self.updated = self.created
        self.access_count = 0

    def add_evidence(self, evidence: str, weight: float = 0.1):
        self.evidence.append({"text": evidence, "weight": weight, "timestamp": datetime.now(timezone.utc).isoformat()})
        self._recalc_confidence()
        self.updated = datetime.now(timezone.utc).isoformat()

    def add_contradiction(self, contradiction: str, weight: float = 0.1):
        self.contradictions.append({"text": contradiction, "weight": weight, "timestamp": datetime.now(timezone.utc).isoformat()})
        self._recalc_confidence()
        self.updated = datetime.now(timezone.utc).isoformat()

    def _recalc_confidence(self):
        ev_score = sum(e["weight"] for e in self.evidence)
        ct_score = sum(c["weight"] for c in self.contradictions)
        total = ev_score + ct_score + 1e-8
        self.confidence = max(0.0, min(1.0, (ev_score + 0.5) / total))
        self.confidence = round(self.confidence, 4)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class TruthBudget:
    def __init__(self, max_budget: float = 100.0):
        self.max_budget = max_budget
        self.used = 0.0
        self.history = []

    def can_assert(self, confidence: float) -> bool:
        cost = (1.0 - confidence) * 10
        return (self.used + cost) <= self.max_budget

    def spend(self, confidence: float, claim: str):
        cost = (1.0 - confidence) * 10
        self.used += cost
        self.history.append({
            "claim": claim[:80],
            "confidence": confidence,
            "cost": round(cost, 4),
            "remaining": round(self.max_budget - self.used, 4),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def reset(self):
        self.used = 0.0
        self.history = []

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoTruthEngine:
    """
    Anti-Hallucination Truth Engine.
    Verifies claims, tracks confidence, detects contradictions,
    and enforces truth budgets.
    """

    VERIFICATION_LEVELS = {"quick": 0.3, "standard": 0.6, "deep": 0.9}

    def __init__(self, knowledge_core=None):
        self.facts = {}  # id -> FactRecord
        self.budget = TruthBudget()
        self.knowledge_core = knowledge_core
        self.claim_index = defaultdict(list)  # normalized claim -> [fact_ids]
        self.source_reliability = defaultdict(lambda: 0.5)
        self._init_sources()

    def _init_sources(self):
        self.source_reliability["user_input"] = 0.3
        self.source_reliability["observation"] = 0.6
        self.source_reliability["inference"] = 0.4
        self.source_reliability["verified_knowledge"] = 0.9
        self.source_reliability["external_api"] = 0.7
        self.source_reliability["self_generated"] = 0.35
        self.source_reliability["training_data"] = 0.8
        self.source_reliability["user_correction"] = 0.5

    # ── Fact Registration ─────────────────────────────────────────────

    def register_fact(self, claim: str, confidence: float = 0.5,
                      source: str = "unknown", category: str = "general",
                      evidence: list = None, tags: list = None) -> dict:
        if not self.budget.can_assert(confidence):
            return {"success": False, "error": "Truth budget exceeded", "fact_id": None}

        existing = self._find_similar_claim(claim)
        if existing:
            existing.add_evidence(f"Duplicate registration: {claim}", 0.05)
            self.budget.spend(confidence, claim)
            return {"success": True, "fact_id": existing.id, "merged": True}

        fact = FactRecord(claim, confidence, source, category, evidence, tags=tags)
        self.facts[fact.id] = fact
        norm = self._normalize_claim(claim)
        self.claim_index[norm].append(fact.id)
        self.budget.spend(confidence, claim)
        return {"success": True, "fact_id": fact.id, "merged": False}

    def register_claim(self, claim: str, context: dict = None) -> dict:
        context = context or {}
        source = context.get("source", "unknown")
        category = context.get("category", "general")
        initial_conf = self.source_reliability.get(source, 0.3)
        return self.register_fact(claim, initial_conf, source, category)

    # ── Truth Score Computation ───────────────────────────────────────

    def compute_truth_score(self, claim: str, level: str = "standard") -> dict:
        if level not in self.VERIFICATION_LEVELS:
            level = "standard"
        threshold = self.VERIFICATION_LEVELS[level]

        norm = self._normalize_claim(claim)
        matches = self.claim_index.get(norm, [])
        direct_facts = [self.facts[fid] for fid in matches if fid in self.facts]

        if not direct_facts:
            # No direct match, check semantic similarity
            similar = self._semantic_search(claim, top_k=3)
            if similar:
                avg_conf = sum(s["fact"].confidence for s in similar) / len(similar)
                source_boost = max(s["fact"].source == "verified_knowledge" for s in similar)
                score = avg_conf * (1.1 if source_boost else 1.0)
            else:
                score = 0.3  # unknown claim, low default
        else:
            best = max(direct_facts, key=lambda f: f.confidence)
            score = best.confidence
            # boost if verified
            if best.verified:
                score = min(1.0, score + 0.15)

        # Check for contradictions
        contradiction_penalty = 0.0
        contradictions_found = []
        for fid, fact in self.facts.items():
            if fid in matches:
                continue
            if self._claims_conflict(claim, fact.claim):
                contradiction_penalty += 0.15 * (1.0 - fact.confidence)
                if len(contradictions_found) < 5:
                    contradictions_found.append(fact.claim[:100])

        score = max(0.0, min(1.0, score - contradiction_penalty))

        # Apply verification level threshold
        if level == "quick" and score >= threshold:
            status = "likely_true"
        elif level == "standard" and score >= threshold:
            status = "plausible"
        elif level == "deep" and score >= threshold:
            status = "verified"
        else:
            status = "uncertain"

        return {
            "claim": claim[:200],
            "truth_score": round(score, 4),
            "status": status,
            "verification_level": level,
            "contradictions_found": contradictions_found,
            "direct_matches": len(direct_facts),
            "budget_remaining": round(self.budget.max_budget - self.budget.used, 2),
        }

    # ── Contradiction Detection ───────────────────────────────────────

    def detect_contradictions(self, claim: str) -> list:
        results = []
        norm = self._normalize_claim(claim)
        for fid, fact in self.facts.items():
            if self._claims_conflict(claim, fact.claim):
                results.append({
                    "fact_id": fact.id,
                    "existing_claim": fact.claim[:150],
                    "confidence": fact.confidence,
                    "contradiction_score": self._contradiction_score(claim, fact.claim),
                })
        results.sort(key=lambda r: -r["contradiction_score"])
        return results[:10]

    def _claims_conflict(self, c1: str, c2: str) -> bool:
        n1, n2 = self._normalize_claim(c1), self._normalize_claim(c2)
        if n1 == n2:
            return False
        words1, words2 = set(n1.split()), set(n2.split())
        if len(words1) < 2 or len(words2) < 2:
            return False
        overlap = len(words1 & words2) / max(len(words1 | words2), 1)
        if overlap < 0.2:
            return False
        negations1 = {"not", "no", "never", "cannot", "isn't", "doesn't", "won't", "don't"}
        negations2 = {"not", "no", "never", "cannot", "isn't", "doesn't", "won't", "don't"}
        has_neg1 = bool(words1 & negations1)
        has_neg2 = bool(words2 & negations2)
        if has_neg1 != has_neg2 and overlap > 0.3:
            return True
        return False

    def _contradiction_score(self, c1: str, c2: str) -> float:
        n1, n2 = self._normalize_claim(c1), self._normalize_claim(c2)
        words1, words2 = set(n1.split()), set(n2.split())
        if not words1 or not words2:
            return 0.0
        overlap = len(words1 & words2) / max(len(words1 | words2), 1)
        return overlap if self._claims_conflict(c1, c2) else 0.0

    # ── Verification ──────────────────────────────────────────────────

    def verify(self, claim: str, level: str = "standard") -> dict:
        score = self.compute_truth_score(claim, level)
        fact_id = None
        if score["truth_score"] >= self.VERIFICATION_LEVELS.get(level, 0.6):
            result = self.register_fact(claim, score["truth_score"], "verification",
                                        evidence=[f"Verified at {level} level"])
            fact_id = result.get("fact_id")
            if fact_id and fact_id in self.facts:
                self.facts[fact_id].verified = True
                self.facts[fact_id].verification_level = level
        return {**score, "fact_id": fact_id}

    # ── Helpers ───────────────────────────────────────────────────────

    def _normalize_claim(self, claim: str) -> str:
        c = claim.lower().strip()
        c = re.sub(r'[^\w\s]', '', c)
        c = re.sub(r'\s+', ' ', c)
        return c[:200]

    def _find_similar_claim(self, claim: str) -> Optional[FactRecord]:
        norm = self._normalize_claim(claim)
        if norm in self.claim_index:
            fid = self.claim_index[norm][0]
            return self.facts.get(fid)
        for fid, fact in self.facts.items():
            if self._normalize_claim(fact.claim) == norm:
                return fact
        return None

    def _semantic_search(self, query: str, top_k: int = 3) -> list:
        q_words = set(self._normalize_claim(query).split())
        scored = []
        for fid, fact in self.facts.items():
            f_words = set(self._normalize_claim(fact.claim).split())
            if not q_words or not f_words:
                continue
            overlap = len(q_words & f_words) / max(len(q_words | f_words), 1)
            if overlap > 0.15:
                scored.append({"fact": fact, "score": overlap})
        scored.sort(key=lambda s: -s["score"])
        return scored[:top_k]

    def get_fact(self, fact_id: str) -> Optional[dict]:
        fact = self.facts.get(fact_id)
        if fact:
            fact.access_count += 1
            return fact.to_dict()
        return None

    def search_facts(self, query: str, top_k: int = 10) -> list:
        results = self._semantic_search(query, top_k)
        return [r["fact"].to_dict() for r in results]

    def get_stats(self) -> dict:
        if not self.facts:
            return {"total_facts": 0, "avg_confidence": 0, "verified": 0, "budget_used": 0}
        confs = [f.confidence for f in self.facts.values()]
        return {
            "total_facts": len(self.facts),
            "avg_confidence": round(sum(confs) / len(confs), 4),
            "verified": sum(1 for f in self.facts.values() if f.verified),
            "budget_used": round(self.budget.used, 2),
            "budget_remaining": round(self.budget.max_budget - self.budget.used, 2),
            "unique_sources": len(set(f.source for f in self.facts.values())),
        }

    def save(self) -> dict:
        return {
            "facts": {fid: f.to_dict() for fid, f in self.facts.items()},
            "budget": self.budget.to_dict(),
            "source_reliability": dict(self.source_reliability),
        }

    def load(self, data: dict):
        self.facts = {}
        self.claim_index = defaultdict(list)
        for fid, fd in data.get("facts", {}).items():
            f = FactRecord(fd.get("claim", ""), fd.get("confidence", 0.5),
                           fd.get("source", "unknown"))
            f.__dict__.update(fd)
            self.facts[fid] = f
            norm = self._normalize_claim(f.claim)
            self.claim_index[norm].append(fid)
        bd = data.get("budget", {})
        self.budget = TruthBudget(bd.get("max_budget", 100.0))
        self.budget.__dict__.update(bd)
        self.source_reliability.update(data.get("source_reliability", {}))
