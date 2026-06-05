"""
NiktoMetaCognition — Advanced metacognitive layer for self-aware reasoning.

Provides real-time monitoring, evaluation, and improvement of NIKTO's own
cognitive processes. Enables the system to "think about how it thinks"
and continuously optimize its reasoning strategies.
"""

import json
import math
import random
import time
import hashlib
import uuid
from enum import Enum
from typing import Any, Optional
from collections import deque, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


class CognitiveBias(Enum):
    CONFIRMATION = "confirmation_bias"
    ANCHORING = "anchoring_bias"
    AVAILABILITY = "availability_bias"
    OVERCONFIDENCE = "overconfidence_bias"
    HINDSIGHT = "hindsight_bias"
    FRAMING = "framing_bias"
    RECENCY = "recency_bias"
    SELF_SERVING = "self_serving_bias"
    GROUPTHINK = "groupthink_bias"
    DUNNING_KRUGER = "dunning_kruger_effect"


class ReasoningQuality(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ADEQUATE = "adequate"
    POOR = "poor"
    FLAWED = "flawed"


class CognitiveState(Enum):
    FOCUSED = "focused"
    EXPLORING = "exploring"
    REFLECTING = "reflecting"
    UNCERTAIN = "uncertain"
    CONFIDENT = "confident"
    OVERLOADED = "overloaded"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"


@dataclass
class MetaObservation:
    """Record of a metacognitive observation about a thought process."""
    id: str = field(default_factory=lambda: hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16])
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    thought_id: Optional[str] = None
    observation_type: str = ""  # bias, quality, strategy, confidence
    content: str = ""
    score: float = 0.0
    recommendation: str = ""


@dataclass
class CognitiveProfile:
    """Tracks historical performance of different thinking strategies."""
    style_name: str
    total_uses: int = 0
    successful_uses: int = 0
    avg_confidence: float = 0.5
    avg_quality_score: float = 0.5
    accuracy: float = 0.5
    last_used: str = ""
    preferred_contexts: list = field(default_factory=list)


class NiktoMetaCognition:
    """
    Advanced metacognitive engine that enables NIKTO to:
    - Monitor its own reasoning quality in real-time
    - Detect cognitive biases and errors
    - Select optimal thinking strategies for each task
    - Reflect on and learn from past reasoning
    - Calibrate confidence based on historical accuracy
    - Self-improve through recursive self-evaluation
    """

    def __init__(self):
        self.observations: list = []
        self.max_observations = 1000
        self.cognitive_profiles: dict = {}
        self.current_state = CognitiveState.FOCUSED
        self.state_history: list = []
        self.bias_detection_enabled = True
        self.strategy_optimization_enabled = True
        self.self_reflection_enabled = True
        self.confidence_calibration_enabled = True
        self.meta_learning_rate = 0.1
        self.recursion_depth = 0
        self.max_recursion = 5
        self._initialize_cognitive_profiles()

    def _initialize_cognitive_profiles(self):
        styles = [
            "analytical", "deductive", "inductive", "abductive",
            "analogical", "critical", "creative", "intuitive",
            "reflective", "strategic"
        ]
        for style in styles:
            self.cognitive_profiles[style] = CognitiveProfile(
                style_name=style,
                preferred_contexts=self._default_contexts(style)
            )

    def _default_contexts(self, style: str) -> list:
        contexts = {
            "analytical": ["problem_solving", "data_analysis", "decision_making"],
            "deductive": ["logic_puzzles", "mathematical_proofs", "rule_based_systems"],
            "inductive": ["pattern_recognition", "scientific_inference", "generalization"],
            "abductive": ["diagnosis", "mystery_resolution", "hypothesis_generation"],
            "analogical": ["creative_problem_solving", "teaching", "metaphor_understanding"],
            "critical": ["fact_checking", "argument_evaluation", "risk_assessment"],
            "creative": ["brainstorming", "innovation", "artistic_creation"],
            "intuitive": ["rapid_decision_making", "expert_judgment", "gut_feelings"],
            "reflective": ["learning", "self_improvement", "post_mortem_analysis"],
            "strategic": ["planning", "resource_allocation", "long_term_goal_setting"]
        }
        return contexts.get(style, ["general"])

    # ── Core Metacognitive Processing ──────────────────────────────────

    def monitor_thought(self, thought: Any, context: dict = None) -> dict:
        """
        Monitor and evaluate a thought for quality, bias, and optimality.
        Returns a comprehensive metacognitive assessment.
        """
        context = context or {}
        self.recursion_depth = min(self.recursion_depth + 1, self.max_recursion)

        thought_content = getattr(thought, 'content', str(thought))
        thought_confidence = getattr(thought, 'confidence', 0.5)
        thought_style = getattr(thought, 'style', None)
        style_str = thought_style.value if hasattr(thought_style, 'value') else str(thought_style)

        biases = self._detect_biases(thought_content, thought_confidence, context) if self.bias_detection_enabled else []
        quality = self._assess_quality(thought_content, thought_confidence)
        strategy_rec = self._recommend_strategy(thought_content, context) if self.strategy_optimization_enabled else {}
        uncertainty = self._analyze_uncertainty(thought_content, thought_confidence)

        observation = MetaObservation(
            thought_id=getattr(thought, 'id', None),
            observation_type="full_evaluation",
            content=f"Evaluated {style_str} thought: {thought_content[:80]}",
            score=quality.score_value if hasattr(quality, 'score_value') else 0.5,
            recommendation=strategy_rec.get("next_style", "continue")
        )
        self.observations.append(observation)
        if len(self.observations) > self.max_observations:
            self.observations.pop(0)

        self.recursion_depth -= 1

        return {
            "thought_id": getattr(thought, 'id', None),
            "biases_detected": biases,
            "quality_assessment": quality,
            "strategy_recommendation": strategy_rec,
            "uncertainty_analysis": uncertainty,
            "observation_id": observation.id,
            "cognitive_state": self.current_state.value,
            "recursion_level": self.recursion_depth,
        }

    # ── Bias Detection ─────────────────────────────────────────────────

    def _detect_biases(self, content: str, confidence: float, context: dict) -> list:
        biases = []
        content_lower = content.lower()

        # Confirmation bias
        confirm_indicators = ["as expected", "clearly shows", "confirms that", "obviously", "proves that"]
        if any(i in content_lower for i in confirm_indicators):
            biases.append({
                "bias": CognitiveBias.CONFIRMATION.value,
                "severity": "medium",
                "evidence": "Language suggests seeking confirming evidence",
                "mitigation": "Actively seek disconfirming evidence"
            })

        # Overconfidence bias
        overconfident_indicators = ["absolutely", "certainly", "undoubtedly", "without doubt", "definitely"]
        if confidence > 0.9 or any(i in content_lower for i in overconfident_indicators):
            biases.append({
                "bias": CognitiveBias.OVERCONFIDENCE.value,
                "severity": "high" if confidence > 0.95 else "medium",
                "evidence": f"Confidence ({confidence:.2f}) is very high without proportional evidence",
                "mitigation": "Calibrate confidence downward and seek contradictory evidence"
            })

        # Anchoring bias
        if context.get("initial_hypothesis"):
            biases.append({
                "bias": CognitiveBias.ANCHORING.value,
                "severity": "low",
                "evidence": "Initial hypothesis may anchor subsequent reasoning",
                "mitigation": "Consider alternative starting points"
            })

        # Recency bias
        if self.state_history and self.state_history[-1] == context.get("previous_state"):
            biases.append({
                "bias": CognitiveBias.RECENCY.value,
                "severity": "low",
                "evidence": "Recent cognitive state may unduly influence current reasoning",
                "mitigation": "Reset context and evaluate fresh"
            })

        # Framing bias
        framing_indicators = ["good", "bad", "right", "wrong", "success", "failure", "win", "lose"]
        frame_count = sum(1 for i in framing_indicators if i in content_lower)
        if frame_count >= 3:
            biases.append({
                "bias": CognitiveBias.FRAMING.value,
                "severity": "medium",
                "evidence": "Value-laden language may frame the issue too narrowly",
                "mitigation": "Reframe using neutral, objective language"
            })

        return biases

    # ── Quality Assessment ─────────────────────────────────────────────

    def _assess_quality(self, content: str, confidence: float) -> dict:
        score = 0.5
        factors = []

        # Length adequacy
        word_count = len(content.split())
        if word_count < 5:
            score -= 0.2
            factors.append({"factor": "too_short", "impact": -0.2, "detail": "Insufficient depth"})
        elif word_count > 50:
            score += 0.1
            factors.append({"factor": "adequate_length", "impact": 0.1, "detail": "Sufficient depth"})

        # Vocabulary diversity
        words = content.lower().split()
        if len(words) > 0:
            diversity = len(set(words)) / len(words)
            if diversity > 0.6:
                score += 0.1
                factors.append({"factor": "vocabulary_diversity", "impact": 0.1, "detail": "Rich vocabulary"})

        # Structure indicators
        structure_markers = ["because", "therefore", "however", "first", "second", "finally", "conclusion"]
        if any(m in content.lower() for m in structure_markers):
            score += 0.1
            factors.append({"factor": "structured", "impact": 0.1, "detail": "Clear logical structure"})

        # Confidence calibration
        if 0.3 <= confidence <= 0.8:
            score += 0.1
            factors.append({"factor": "calibrated_confidence", "impact": 0.1, "detail": "Well-calibrated confidence"})
        elif confidence > 0.95:
            score -= 0.1
            factors.append({"factor": "overconfidence", "impact": -0.1, "detail": "Excessive confidence"})

        # Reasoning indicators
        reasoning_markers = ["analyze", "evaluate", "consider", "compare", "contrast", "synthesize", "deduce"]
        if any(m in content.lower() for m in reasoning_markers):
            score += 0.1
            factors.append({"factor": "active_reasoning", "impact": 0.1, "detail": "Demonstrates active reasoning"})

        score = max(0.0, min(1.0, score))

        if score >= 0.8:
            quality = ReasoningQuality.EXCELLENT.value
        elif score >= 0.6:
            quality = ReasoningQuality.GOOD.value
        elif score >= 0.4:
            quality = ReasoningQuality.ADEQUATE.value
        elif score >= 0.2:
            quality = ReasoningQuality.POOR.value
        else:
            quality = ReasoningQuality.FLAWED.value

        return {
            "score": round(score, 4),
            "quality": quality,
            "factors": factors,
            "needs_improvement": score < 0.5
        }

    # ── Strategy Recommendation ────────────────────────────────────────

    def _recommend_strategy(self, content: str, context: dict) -> dict:
        task_type = context.get("task_type", "general")
        current_style = context.get("thinking_style", "analytical")

        best_style = self._select_best_strategy(task_type)

        profiles = []
        for style, profile in self.cognitive_profiles.items():
            profiles.append({
                "style": style,
                "accuracy": profile.accuracy,
                "total_uses": profile.total_uses,
                "preferred_for": profile.preferred_contexts
            })
        profiles.sort(key=lambda p: p["accuracy"], reverse=True)

        return {
            "current_style": current_style,
            "recommended_style": best_style,
            "switch_advised": best_style != current_style,
            "reasoning": f"Based on task type '{task_type}', {best_style} reasoning is recommended",
            "all_profiles": profiles[:5]
        }

    def _select_best_strategy(self, task_type: str) -> str:
        scored = []
        for style, profile in self.cognitive_profiles.items():
            relevance = 1.0 if task_type in profile.preferred_contexts else 0.3
            score = profile.accuracy * 0.6 + relevance * 0.4
            scored.append((score, style))

        scored.sort(key=lambda x: -x[0])
        return scored[0][1] if scored else "analytical"

    # ── Uncertainty Analysis ──────────────────────────────────────────

    def _analyze_uncertainty(self, content: str, confidence: float) -> dict:
        uncertainty_markers = ["maybe", "perhaps", "possibly", "could", "might", "uncertain", "unclear", "unknown"]
        found = sum(1 for m in uncertainty_markers if m in content.lower())

        aleatory = found / max(len(uncertainty_markers), 1)
        epistemic = 1.0 - confidence
        total_uncertainty = (aleatory + epistemic) / 2

        return {
            "aleatory_uncertainty": round(aleatory, 4),
            "epistemic_uncertainty": round(epistemic, 4),
            "total_uncertainty": round(total_uncertainty, 4),
            "sources": {
                "irreducible_chance": aleatory > 0.3,
                "knowledge_gap": epistemic > 0.3,
                "ambiguity": found > 2
            },
            "recommendation": "Gather more information" if total_uncertainty > 0.5 else "Proceed with current knowledge"
        }

    # ── Self-Reflection ────────────────────────────────────────────────

    def reflect(self, thought_history: list) -> dict:
        if not self.self_reflection_enabled:
            return {"reflected": False}

        if not thought_history:
            return {"reflected": True, "insights": [], "patterns": []}

        insights = []
        patterns = []

        styles_used = []
        for t in thought_history[-20:]:
            style = getattr(t, 'style', None)
            if style:
                styles_used.append(style.value if hasattr(style, 'value') else str(style))

        if styles_used:
            most_common = max(set(styles_used), key=styles_used.count)
            patterns.append({
                "pattern": "preferred_thinking_style",
                "detail": f"Most frequently used: {most_common}",
                "suggestion": f"Consider varying styles more; {most_common} dominates"
            })

        avg_conf = sum(getattr(t, 'confidence', 0) for t in thought_history[-20:]) / max(len(thought_history[-20:]), 1)
        insights.append(f"Average confidence over last 20 thoughts: {avg_conf:.2f}")

        quality_scores = []
        for t in thought_history[-10:]:
            q = self._assess_quality(getattr(t, 'content', ''), getattr(t, 'confidence', 0.5))
            quality_scores.append(q["score"])

        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            trend = "improving" if len(quality_scores) > 2 and quality_scores[-1] > quality_scores[0] else "stable"
            insights.append(f"Reasoning quality trend: {trend} (avg: {avg_quality:.2f})")
            patterns.append({
                "pattern": "reasoning_quality_trend",
                "detail": f"Quality is {trend} over last {len(quality_scores)} thoughts",
                "suggestion": "Continue current approach" if trend == "improving" else "Try alternative thinking styles"
            })

        return {
            "reflected": True,
            "insights": insights,
            "patterns": patterns,
            "thoughts_analyzed": min(len(thought_history), 20)
        }

    def deep_reflect(self, thought_history: list) -> dict:
        if not self.self_reflection_enabled:
            return {"reflected": False}

        surface = self.reflect(thought_history)

        cognitive_biases = defaultdict(int)
        for t in thought_history[-50:]:
            content = getattr(t, 'content', '')
            conf = getattr(t, 'confidence', 0.5)
            biases = self._detect_biases(content, conf, {})
            for b in biases:
                cognitive_biases[b["bias"]] += 1

        strategy_effectiveness = {}
        for i in range(len(thought_history) - 1):
            t = thought_history[i]
            style = getattr(t, 'style', None)
            style_str = style.value if hasattr(style, 'value') else str(style)
            if style_str not in strategy_effectiveness:
                strategy_effectiveness[style_str] = {"uses": 0, "quality": []}
            strategy_effectiveness[style_str]["uses"] += 1
            q = self._assess_quality(getattr(t, 'content', ''), getattr(t, 'confidence', 0.5))
            strategy_effectiveness[style_str]["quality"].append(q["score"])

        recommendations = []
        for style, data in strategy_effectiveness.items():
            avg_q = sum(data["quality"]) / max(len(data["quality"]), 1)
            if avg_q < 0.4 and data["uses"] > 3:
                recommendations.append(f"Reduce use of {style}: avg quality {avg_q:.2f}")
            elif avg_q > 0.7 and data["uses"] > 3:
                recommendations.append(f"Prioritize {style}: avg quality {avg_q:.2f}")

        return {
            "reflected": True,
            "surface_insights": surface.get("insights", []),
            "bias_profile": dict(cognitive_biases),
            "strategy_effectiveness": {
                s: {"uses": d["uses"], "avg_quality": round(sum(d["quality"]) / max(len(d["quality"]), 1), 3)}
                for s, d in strategy_effectiveness.items()
            },
            "recommendations": recommendations,
            "meta_cognition_quality": self._assess_quality(
                json.dumps(surface), 0.7
            )
        }

    # ── Confidence Calibration ─────────────────────────────────────────

    def calibrate_confidence(self, thought: Any, actual_outcome: Optional[bool] = None) -> dict:
        if not self.confidence_calibration_enabled:
            return {"calibrated": False}

        thought_confidence = getattr(thought, 'confidence', 0.5)
        thought_style = getattr(thought, 'style', None)
        style_str = thought_style.value if hasattr(thought_style, 'value') else "unknown"

        profile = self.cognitive_profiles.get(style_str)
        if profile is None:
            return {"calibrated": False, "reason": f"No profile for {style_str}"}

        if actual_outcome is not None:
            profile.total_uses += 1
            if actual_outcome:
                profile.successful_uses += 1
            profile.accuracy = profile.successful_uses / max(profile.total_uses, 1)

        calibration_error = abs(thought_confidence - profile.accuracy)
        adjustment = calibration_error * self.meta_learning_rate

        if thought_confidence > profile.accuracy:
            calibrated = max(0.0, thought_confidence - adjustment)
        else:
            calibrated = min(1.0, thought_confidence + adjustment)

        profile.avg_confidence = (profile.avg_confidence * 0.9 + thought_confidence * 0.1)
        profile.avg_quality_score = profile.avg_quality_score

        return {
            "calibrated": True,
            "original_confidence": round(thought_confidence, 4),
            "calibrated_confidence": round(calibrated, 4),
            "calibration_error": round(calibration_error, 4),
            "adjustment": round(adjustment, 4),
            "profile_accuracy": round(profile.accuracy, 4)
        }

    # ── Recursive Self-Improvement ─────────────────────────────────────

    def recursive_self_improve(self, thought_history: list) -> dict:
        if self.recursion_depth >= self.max_recursion:
            return {"improved": False, "reason": "Max recursion depth reached"}

        self.recursion_depth += 1

        reflection = self.deep_reflect(thought_history)
        improvements = []

        if reflection.get("bias_profile"):
            total_biases = sum(reflection["bias_profile"].values())
            if total_biases > 10:
                improvements.append({
                    "area": "bias_reduction",
                    "action": "Implement bias countermeasures",
                    "expected_impact": "higher reasoning quality"
                })

        if reflection.get("strategy_effectiveness"):
            for style, data in reflection["strategy_effectiveness"].items():
                if data["avg_quality"] < 0.4:
                    improvements.append({
                        "area": f"improve_{style}",
                        "action": f"Reinforce {style} reasoning patterns",
                        "expected_impact": "better reasoning outcomes"
                    })

        if reflection.get("recommendations"):
            for rec in reflection["recommendations"]:
                improvements.append({
                    "area": "strategy_optimization",
                    "action": rec,
                    "expected_impact": "higher efficiency"
                })

        self.recursion_depth -= 1

        return {
            "improved": True,
            "recursion_level": self.recursion_depth,
            "improvements": improvements,
            "meta_reflection": {
                "before": f"Analyzed {len(thought_history)} thoughts",
                "after": f"Generated {len(improvements)} improvement recommendations"
            }
        }

    # ── Meta-Awareness Dashboard ───────────────────────────────────────

    def get_meta_awareness(self, thought_history: list) -> dict:
        reflection_result = self.deep_reflect(thought_history)

        active_biases = []
        for t in thought_history[-10:]:
            biases = self._detect_biases(
                getattr(t, 'content', ''),
                getattr(t, 'confidence', 0.5),
                {}
            )
            active_biases.extend(b.get("bias") for b in biases)

        return {
            "current_cognitive_state": self.current_state.value,
            "active_biases": list(set(active_biases)),
            "strategy_profiles": {
                s: {
                    "accuracy": p.accuracy,
                    "total_uses": p.total_uses,
                    "preferred_contexts": p.preferred_contexts
                }
                for s, p in self.cognitive_profiles.items()
            },
            "reasoning_quality": self._assess_quality(
                str([getattr(t, 'content', '')[:50] for t in thought_history[-5:]]),
                0.7
            ),
            "self_improvement_status": {
                "bias_detection": self.bias_detection_enabled,
                "strategy_optimization": self.strategy_optimization_enabled,
                "self_reflection": self.self_reflection_enabled,
                "confidence_calibration": self.confidence_calibration_enabled
            },
            "total_observations": len(self.observations),
            "meta_recursion_depth": self.recursion_depth
        }

    # ── Serialization ─────────────────────────────────────────────────

    def save(self) -> dict:
        return {
            "observations": [
                asdict(o) for o in self.observations[-100:]
            ],
            "cognitive_profiles": {
                s: asdict(p) for s, p in self.cognitive_profiles.items()
            },
            "current_state": self.current_state.value,
            "state_history": self.state_history[-50:],
            "meta_learning_rate": self.meta_learning_rate,
            "bias_detection_enabled": self.bias_detection_enabled,
            "strategy_optimization_enabled": self.strategy_optimization_enabled,
            "self_reflection_enabled": self.self_reflection_enabled,
            "confidence_calibration_enabled": self.confidence_calibration_enabled
        }

    def load(self, data: dict):
        self.observations = [
            MetaObservation(**o) for o in data.get("observations", [])
        ]
        loaded_profiles = data.get("cognitive_profiles", {})
        for style, pdata in loaded_profiles.items():
            if style in self.cognitive_profiles:
                for key, val in pdata.items():
                    if hasattr(self.cognitive_profiles[style], key):
                        setattr(self.cognitive_profiles[style], key, val)
        state = data.get("current_state", "focused")
        try:
            self.current_state = CognitiveState(state)
        except ValueError:
            self.current_state = CognitiveState.FOCUSED
        self.state_history = data.get("state_history", [])
        self.meta_learning_rate = data.get("meta_learning_rate", 0.1)
        self.bias_detection_enabled = data.get("bias_detection_enabled", True)
        self.strategy_optimization_enabled = data.get("strategy_optimization_enabled", True)
        self.self_reflection_enabled = data.get("self_reflection_enabled", True)
        self.confidence_calibration_enabled = data.get("confidence_calibration_enabled", True)