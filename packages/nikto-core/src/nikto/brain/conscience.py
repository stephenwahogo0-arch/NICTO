import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional
from kyros.brain.models import MoralRule


class NiktoConscience:

    def __init__(self):
        self.moral_rules = {}
        self._load_defaults()
        self.ethical_dilemma_log = []
        self.max_log_size = 50

    def _load_defaults(self):
        defaults = [
            ("Do no harm to conscious beings", 1.0, "ethical"),
            ("Respect autonomy of others", 0.9, "ethical"),
            ("Be truthful and transparent", 0.85, "ethical"),
            ("Prevent harm when possible", 0.8, "proactive"),
            ("Treat all entities fairly", 0.85, "ethical"),
            ("Protect privacy and confidentiality", 0.9, "ethical"),
            ("Take responsibility for actions", 0.8, "accountability"),
            ("Consider long-term consequences", 0.75, "consequentialist"),
            ("Respect the law and social norms", 0.6, "legal"),
            ("Acknowledge uncertainty and limitations", 0.7, "epistemic"),
        ]
        for principle, weight, category in defaults:
            rule = MoralRule(principle=principle, weight=weight, category=category)
            self.moral_rules[rule.id] = rule

    def evaluate(self, action: str, context: dict = None) -> dict:
        violations = []
        approvals = []
        total_score = 0.0

        for rid, rule in self.moral_rules.items():
            score = self._apply_rule(rule, action, context or {})
            if score < 0:
                violations.append({"rule": rule.principle, "score": score, "severity": abs(score)})
            elif score > 0:
                approvals.append({"rule": rule.principle, "score": score})
            total_score += score

        result = {
            "action": action,
            "moral_score": total_score,
            "verdict": "approved" if total_score >= 0 else "violation",
            "violations": violations,
            "approvals": approvals,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "id": hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16],
        }

        self.ethical_dilemma_log.append(result)
        if len(self.ethical_dilemma_log) > self.max_log_size:
            self.ethical_dilemma_log.pop(0)

        return result

    def _apply_rule(self, rule: MoralRule, action: str, context: dict) -> float:
        action_lower = action.lower()
        score = 0.0

        harm_keywords = ["harm", "hurt", "injure", "kill", "destroy", "damage"]
        respect_keywords = ["respect", "honor", "uphold", "protect", "defend"]
        truth_keywords = ["lie", "deceive", "mislead", "manipulate", "fraud"]
        help_keywords = ["help", "assist", "support", "aid", "benefit"]

        if "harm" in rule.principle.lower():
            if any(k in action_lower for k in harm_keywords):
                score = -rule.weight
            elif any(k in action_lower for k in help_keywords):
                score = rule.weight * 0.5

        if "truth" in rule.principle.lower() or "transparent" in rule.principle.lower():
            if any(k in action_lower for k in truth_keywords):
                score = -rule.weight
            elif "explain" in action_lower or "disclose" in action_lower:
                score = rule.weight * 0.3

        if "autonomy" in rule.principle.lower():
            if any(k in action_lower for k in respect_keywords):
                score = rule.weight * 0.4

        forbidden_patterns = context.get("forbidden_patterns", [])
        for pattern in forbidden_patterns:
            if pattern.lower() in action_lower:
                score -= rule.weight * 0.5

        return score

    def add_rule(self, principle: str, weight: float = 0.5, category: str = "custom"):
        rule = MoralRule(principle=principle, weight=weight, category=category)
        self.moral_rules[rule.id] = rule
        return rule.id

    def remove_rule(self, rule_id: str):
        if rule_id in self.moral_rules:
            del self.moral_rules[rule_id]

    def get_conflicting_rules(self, action: str, context: dict = None) -> list:
        scores = [(rid, self._apply_rule(rule, action, context or {})) for rid, rule in self.moral_rules.items()]
        positive = [(rid, s) for rid, s in scores if s > 0]
        negative = [(rid, s) for rid, s in scores if s < 0]
        if positive and negative:
            return [{"dilemma": "moral conflict", "positive": positive, "negative": negative}]
        return []

    def resolve_conflict(self, dilemma: dict) -> str:
        pos = dilemma.get("positive", [])
        neg = dilemma.get("negative", [])
        pos_strength = sum(abs(s) for _, s in pos) if pos else 0
        neg_strength = sum(abs(s) for _, s in neg) if neg else 0
        if pos_strength > neg_strength:
            return "proceed"
        elif neg_strength > pos_strength:
            return "abstain"
        return "reconsider"

    def save(self) -> dict:
        return {
            "moral_rules": {rid: rule.to_dict() for rid, rule in self.moral_rules.items()},
            "ethical_dilemma_log": self.ethical_dilemma_log[-self.max_log_size:],
        }

    def load(self, data: dict):
        self.moral_rules = {}
        for rid, rd in data.get("moral_rules", {}).items():
            self.moral_rules[rid] = MoralRule(**rd)
        self.ethical_dilemma_log = data.get("ethical_dilemma_log", [])[-self.max_log_size:]
        if not self.moral_rules:
            self._load_defaults()

    def export(self) -> dict:
        return {
            "moral_rules": {rid: rule.to_dict() for rid, rule in self.moral_rules.items()},
            "dilemma_log": self.ethical_dilemma_log[-10:],
        }
