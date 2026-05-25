"""NIKTO Reasoner — Multi-style reasoning engine with self-correction and uncertainty quantification."""

import json
import random
import math
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

try:
    from nikto.brain.models import ThinkingStyle, Thought
except ImportError:
    try:
        from kyros.brain.models import ThinkingStyle, Thought
    except ImportError:
        from enum import Enum
        class ThinkingStyle(Enum):
            DEDUCTIVE = "deductive"
            INDUCTIVE = "inductive"
            ABDUCTIVE = "abductive"
            ANALOGICAL = "analogical"
            CRITICAL = "critical"
            CREATIVE = "creative"
            INTUITIVE = "intuitive"
            ANALYTICAL = "analytical"
            REFLECTIVE = "reflective"
            STRATEGIC = "strategic"
        from dataclasses import dataclass, field, asdict
        @dataclass
        class Thought:
            content: str; style: ThinkingStyle = ThinkingStyle.ANALYTICAL
            confidence: float = 0.5
            timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
            id: str = field(default_factory=lambda: hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16])
            parent_id: Optional[str] = None; metadata: dict = field(default_factory=dict)
            def to_dict(self) -> dict: d = asdict(self); d["style"] = self.style.value; return d
            def __post_init__(self): self.confidence = max(0.0, min(1.0, self.confidence))


class NiktoReasoner:

    def __init__(self):
        self.thought_history = []
        self.max_history = 200
        self.confidence_threshold = 0.4
        self.thinking_depth = 3
        self.metacognition_enabled = True

    def think(self, prompt: str, style: ThinkingStyle = ThinkingStyle.ANALYTICAL,
              context: dict = None) -> Thought:
        method = getattr(self, f"_think_{style.value}", self._think_analytical)
        thought = method(prompt, context or {})
        self.thought_history.append(thought)
        if len(self.thought_history) > self.max_history:
            self.thought_history.pop(0)
        return thought

    def chain_of_thought(self, prompt: str, style: ThinkingStyle = ThinkingStyle.ANALYTICAL,
                         depth: int = None) -> list:
        depth = depth or self.thinking_depth
        chain = []
        current_prompt = prompt
        for i in range(depth):
            thought = self.think(current_prompt, style)
            chain.append(thought)
            if i < depth - 1:
                current_prompt = f"Building on: {thought.content}. Next step: {prompt} (iteration {i + 2})"
        return chain

    # ── Self-Corrective Chain ─────────────────────────────────────────

    def self_corrective_chain(self, prompt: str, max_iterations: int = 3,
                              style: ThinkingStyle = ThinkingStyle.ANALYTICAL) -> dict:
        chain = []
        current = prompt
        for i in range(max_iterations):
            thought = self.think(current, style)
            critique = self._self_critique(thought)
            chain.append({
                "iteration": i + 1,
                "thought": thought.to_dict(),
                "critique": critique,
            })
            if critique.get("score", 0) >= 0.8:
                break
            current = f"Previous attempt: {thought.content}. Improve: {prompt}"
        improvement = 0.0
        if len(chain) >= 2:
            first_conf = chain[0]["thought"]["confidence"]
            last_conf = chain[-1]["thought"]["confidence"]
            improvement = last_conf - first_conf
        return {
            "prompt": prompt,
            "iterations": len(chain),
            "chain": chain,
            "final_thought": chain[-1]["thought"],
            "improvement": round(improvement, 4),
        }

    def _self_critique(self, thought: Thought) -> dict:
        issues = []
        score = 0.5
        if thought.confidence < self.confidence_threshold:
            issues.append("Low confidence")
            score -= 0.15
        if len(thought.content) < 20:
            issues.append("Insufficient depth")
            score -= 0.1
        if len(thought.content) > 500:
            issues.append("Excessive verbosity")
            score -= 0.05
        words = thought.content.split()
        if len(set(words)) / max(len(words), 1) < 0.3:
            issues.append("Repetitive language")
            score -= 0.1
        score = max(0.0, min(1.0, score))
        return {"score": round(score, 4), "issues": issues, "needs_revision": score < 0.6}

    # ── Counterfactual Reasoning ──────────────────────────────────────

    def counterfactual_reasoning(self, prompt: str, alternatives: int = 3) -> dict:
        scenarios = []
        for i in range(alternatives):
            alt_prompt = self._generate_counterfactual(prompt, i)
            thought = self.think(alt_prompt, ThinkingStyle.ABDUCTIVE)
            scenarios.append({
                "scenario": f"Alternative {i + 1}",
                "assumption_modified": alt_prompt[:80],
                "thought": thought.to_dict(),
            })
        synthesis = self._synthesize_counterfactuals(prompt, scenarios)
        return {
            "prompt": prompt,
            "alternatives_generated": alternatives,
            "scenarios": scenarios,
            "synthesis": synthesis,
            "key_insight": f"Across {alternatives} alternatives, exploring what-if modifications reveals "
                           f"the sensitivity of '{prompt[:60]}' to underlying assumptions.",
        }

    def _generate_counterfactual(self, prompt: str, idx: int) -> str:
        modifiers = [
            f"What if the opposite were true: NOT ({prompt})?",
            f"Consider if key constraints were removed: {prompt}",
            f"Imagine the inverse scenario: instead of '{prompt[:50]}', consider the reverse.",
            f"What if all known assumptions about '{prompt[:50]}' were wrong?",
            f"Suppose the desired outcome is achieved, trace backwards: {prompt[:50]}",
        ]
        mod = modifiers[idx % len(modifiers)]
        return f"{mod} Explore this counterfactual thoroughly."

    def _synthesize_counterfactuals(self, prompt: str, scenarios: list) -> str:
        styles_used = [s["thought"]["style"] for s in scenarios]
        return (
            f"Synthesis of {len(scenarios)} counterfactual paths for '{prompt[:60]}': "
            f"using {', '.join(set(styles_used))} reasoning. "
            f"Convergence across scenarios suggests robust conclusions; "
            f"divergence indicates assumption-sensitivity."
        )

    # ── Multi-Perspective Analysis ────────────────────────────────────

    def multi_perspective(self, prompt: str, perspectives: list = None) -> dict:
        if not perspectives:
            perspectives = ["technical", "ethical", "practical", "strategic", "creative"]
        results = []
        for i, persp in enumerate(perspectives[:6]):
            style = [ThinkingStyle.ANALYTICAL, ThinkingStyle.CRITICAL,
                     ThinkingStyle.DEDUCTIVE, ThinkingStyle.STRATEGIC if hasattr(ThinkingStyle, 'STRATEGIC') else ThinkingStyle.ANALYTICAL,
                     ThinkingStyle.CREATIVE, ThinkingStyle.INTUITIVE][i % 6]
            context = {"perspective": persp}
            thought = self.think(f"[{persp.upper()} perspective] {prompt}", style, context)
            results.append({"perspective": persp, "thought": thought.to_dict(), "style": style.value})
        synthesis = (
            f"Multi-perspective analysis of '{prompt[:60]}' across "
            f"{len(results)} viewpoints: {', '.join(perspectives[:len(results)])}. "
            f"Integrated understanding emerges from synthesizing these diverse angles."
        )
        return {"prompt": prompt, "perspectives": results, "synthesis": synthesis}

    # ── Uncertainty Quantification ────────────────────────────────────

    def quantify_uncertainty(self, thought: Thought) -> dict:
        conf = thought.confidence
        content_len = len(thought.content)
        word_count = len(thought.content.split())
        ambiguity_indicators = ["maybe", "perhaps", "possibly", "could", "might",
                                "uncertain", "unclear", "unknown", "something", "somehow"]
        found_ambiguous = sum(1 for w in ambiguity_indicators if w in thought.content.lower())
        ambiguity_score = min(1.0, found_ambiguous / 3)
        info_density = word_count / max(content_len, 1) if content_len > 0 else 0
        completeness = min(1.0, word_count / 20) * 0.5 + 0.5 * conf
        interval_width = (1.0 - conf) * 0.5 + ambiguity_score * 0.3
        return {
            "thought_id": thought.id,
            "confidence": conf,
            "ambiguity_score": round(ambiguity_score, 4),
            "completeness": round(completeness, 4),
            "information_density": round(info_density, 4),
            "confidence_interval": [
                round(max(0.0, conf - interval_width), 4),
                round(min(1.0, conf + interval_width), 4),
            ],
            "uncertainty_level": "low" if conf > 0.7 else "medium" if conf > 0.4 else "high",
            "needs_more_info": conf < 0.6 or ambiguity_score > 0.3,
        }

    # ── Thinking Style Methods ────────────────────────────────────────

    def _think_analytical(self, prompt: str, context: dict) -> Thought:
        content = self._decompose(prompt)
        return Thought(content=content, style=ThinkingStyle.ANALYTICAL, confidence=0.7)

    def _think_deductive(self, prompt: str, context: dict) -> Thought:
        premises = context.get("premises", [])
        content = self._logical_deduction(prompt, premises)
        return Thought(content=content, style=ThinkingStyle.DEDUCTIVE, confidence=0.8)

    def _think_inductive(self, prompt: str, context: dict) -> Thought:
        observations = context.get("observations", [])
        content = self._induce_generalization(prompt, observations)
        return Thought(content=content, style=ThinkingStyle.INDUCTIVE, confidence=0.6)

    def _think_abductive(self, prompt: str, context: dict) -> Thought:
        observations = context.get("observations", [])
        content = self._best_explanation(prompt, observations)
        return Thought(content=content, style=ThinkingStyle.ABDUCTIVE, confidence=0.5)

    def _think_analogical(self, prompt: str, context: dict) -> Thought:
        source_domain = context.get("source_domain", "general")
        content = self._analogical_reasoning(prompt, source_domain)
        return Thought(content=content, style=ThinkingStyle.ANALOGICAL, confidence=0.55)

    def _think_critical(self, prompt: str, context: dict) -> Thought:
        content = self._critical_analysis(prompt)
        return Thought(content=content, style=ThinkingStyle.CRITICAL, confidence=0.75)

    def _think_creative(self, prompt: str, context: dict) -> Thought:
        content = self._creative_synthesis(prompt, context.get("constraints", []))
        return Thought(content=content, style=ThinkingStyle.CREATIVE, confidence=0.4)

    def _think_intuitive(self, prompt: str, context: dict) -> Thought:
        content = self._intuitive_leap(prompt, context)
        return Thought(content=content, style=ThinkingStyle.INTUITIVE, confidence=0.3)

    def _think_reflective(self, prompt: str, context: dict) -> Thought:
        content = (
            f"Reflecting on: {prompt}. "
            f"Reviewing past experiences related to this topic. "
            f"Considering what was learned previously: {self._generate_conclusion(prompt, 'reflective')}. "
            f"Integrating new insights with existing knowledge."
        )
        return Thought(content=content, style=ThinkingStyle.REFLECTIVE if hasattr(ThinkingStyle, 'REFLECTIVE') else ThinkingStyle.ANALYTICAL, confidence=0.6)

    def _think_strategic(self, prompt: str, context: dict) -> Thought:
        steps = context.get("steps", [])
        steps_str = "; ".join(steps) if steps else "undefined"
        content = (
            f"Strategic analysis of: {prompt}. "
            f"Steps: [{steps_str}]. "
            f"Long-term objectives: {self._generate_conclusion(prompt, 'strategic')}. "
            f"Resource optimization and risk mitigation considered."
        )
        return Thought(content=content, style=ThinkingStyle.STRATEGIC if hasattr(ThinkingStyle, 'STRATEGIC') else ThinkingStyle.ANALYTICAL, confidence=0.65)

    # ── Core Reasoning Helpers ────────────────────────────────────────

    def _decompose(self, prompt: str) -> str:
        steps = [
            f"Analyzing: {prompt}",
            "Identifying key variables and relationships",
            "Evaluating cause and effect",
            f"Conclusion: Based on systematic analysis, {self._generate_conclusion(prompt, 'analytical')}",
        ]
        return " | ".join(steps)

    def _logical_deduction(self, prompt: str, premises: list) -> str:
        if not premises:
            return f"From first principles: {prompt} → therefore, {self._generate_conclusion(prompt, 'deductive')}"
        chain = " → ".join(premises)
        return f"Premises: {chain} → Conclusion for '{prompt}': {self._generate_conclusion(prompt, 'deductive')}"

    def _induce_generalization(self, prompt: str, observations: list) -> str:
        if not observations:
            return f"From observed patterns in '{prompt}': {self._generate_conclusion(prompt, 'inductive')} (generalization)"
        obs = "; ".join(observations[:3])
        return f"Observed: {obs} → Pattern: {prompt} → Generalized: {self._generate_conclusion(prompt, 'inductive')}"

    def _best_explanation(self, prompt: str, observations: list) -> str:
        if not observations:
            return f"Best explanation for '{prompt}': {self._generate_conclusion(prompt, 'abductive')}"
        obs = "; ".join(observations[:2])
        return f"Given: {obs} → Best explanation: {self._generate_conclusion(prompt, 'abductive')}"

    def _analogical_reasoning(self, prompt: str, source: str) -> str:
        return f"Using analogy from '{source}': {prompt} → Parallel: {self._generate_conclusion(prompt, 'analogical')}"

    def _critical_analysis(self, prompt: str) -> str:
        return (
            f"Critically examining: {prompt} | "
            f"Assumptions: questioning underlying premises | "
            f"Counterarguments: {self._generate_conclusion('counterpoint to ' + prompt, 'critical')} | "
            f"Refined view: {self._generate_conclusion(prompt, 'critical')} (after critical assessment)"
        )

    def _creative_synthesis(self, prompt: str, constraints: list) -> str:
        constraint_note = f" within constraints: {'; '.join(constraints)}" if constraints else ""
        return f"Creative synthesis for '{prompt}'{constraint_note}: {self._generate_conclusion(prompt, 'creative')} (novel combination)"

    def _intuitive_leap(self, prompt: str, context: dict) -> str:
        return f"Intuitive insight on '{prompt}': {self._generate_conclusion(prompt, 'intuitive')} (rapid pattern match)"

    # ── Enhanced Conclusion Generator ─────────────────────────────────

    def _generate_conclusion(self, prompt: str, style: str = "analytical") -> str:
        templates = {
            "analytical": [
                f"a systematic approach reveals optimal solution paths for '{prompt[:50]}'",
                f"multiple evidence streams converge on a coherent understanding of '{prompt[:50]}'",
                f"integrating perspectives yields a nuanced resolution for '{prompt[:50]}'",
                f"the underlying structure of '{prompt[:50]}' becomes clear through analysis",
                f"a balanced evaluation suggests actionable insights for '{prompt[:50]}'",
            ],
            "deductive": [
                f"given the premises, '{prompt[:50]}' necessarily follows",
                f"logical necessity dictates that '{prompt[:50]}' must be the case",
                f"through valid deductive inference, '{prompt[:50]}' is proven",
                f"the conclusion '{prompt[:50]}' is entailed by the premises",
            ],
            "inductive": [
                f"patterns in the data strongly suggest '{prompt[:50]}'",
                f"based on observed instances, '{prompt[:50]}' is a reliable generalization",
                f"the evidence supports the conclusion that '{prompt[:50]}'",
                f"inductive strength indicates '{prompt[:50]}' is highly probable",
            ],
            "abductive": [
                f"the best explanation for the observations is '{prompt[:50]}'",
                f"'[prompt[:50]]' provides the most coherent account of the evidence",
                f"inference to the best explanation points toward '{prompt[:50]}'",
            ],
            "critical": [
                f"after rigorous critique, '{prompt[:50]}' emerges as the most defensible position",
                f"critical examination reveals both strengths and weaknesses in '{prompt[:50]}'",
                f"while '{prompt[:50]}' has merit, several counterarguments warrant consideration",
            ],
            "creative": [
                f"a novel synthesis suggests '{prompt[:50]}' as an innovative approach",
                f"recombining elements yields '{prompt[:50]}' — an unexpected but promising direction",
                f"creative exploration reveals '{prompt[:50]}' as a transformative possibility",
            ],
            "intuitive": [
                f"a rapid pattern match suggests '{prompt[:50]}' feels right",
                f"intuition points strongly toward '{prompt[:50]}' as the natural answer",
                f"without exhaustive analysis, '{prompt[:50]}' emerges as the instinctive conclusion",
            ],
            "reflective": [
                f"reflecting on past experience, '{prompt[:50]}' resonates with prior learning",
                f"integrating new insights with existing knowledge supports '{prompt[:50]}'",
                f"considering the broader context, '{prompt[:50]}' aligns with accumulated wisdom",
            ],
            "strategic": [
                f"long-term optimization favors '{prompt[:50]}' as the strategic choice",
                f"weighing tradeoffs, '{prompt[:50]}' maximizes overall value",
                f"'{prompt[:50]}' represents the optimal path given resource constraints and objectives",
            ],
        }
        candidates = templates.get(style, templates["analytical"])
        return random.choice(candidates)

    # ── Reason, Evaluate, Backtrack ───────────────────────────────────

    def reason(self, prompt: str, context: dict = None) -> Thought:
        context = context or {}
        style_str = context.get("thinking_style", "analytical")
        try:
            style = ThinkingStyle(style_str)
        except ValueError:
            style = ThinkingStyle.ANALYTICAL
        return self.think(prompt, style, context)

    def metacognitive_evaluate(self, thought: Thought) -> dict:
        if not self.metacognition_enabled:
            return {"evaluated": False}
        confidence_issues = []
        if thought.confidence < self.confidence_threshold:
            confidence_issues.append("low_confidence")
        if len(thought.content) < 10:
            confidence_issues.append("insufficient_depth")
        return {
            "evaluated": True,
            "thought_id": thought.id,
            "issues": confidence_issues,
            "needs_revision": len(confidence_issues) > 0,
            "suggested_style": ThinkingStyle.CRITICAL.value if confidence_issues else thought.style.value,
        }

    def backtrack(self, thought_id: str) -> Optional[Thought]:
        for i, t in enumerate(self.thought_history):
            if t.id == thought_id and i > 0:
                return self.thought_history[i - 1]
        return None

    # ── Serialization ─────────────────────────────────────────────────

    def save(self) -> dict:
        return {
            "thought_history": [t.to_dict() for t in self.thought_history],
            "max_history": self.max_history,
            "confidence_threshold": self.confidence_threshold,
            "thinking_depth": self.thinking_depth,
            "metacognition_enabled": self.metacognition_enabled,
        }

    def load(self, data: dict):
        self.max_history = data.get("max_history", 200)
        self.confidence_threshold = data.get("confidence_threshold", 0.4)
        self.thinking_depth = data.get("thinking_depth", 3)
        self.metacognition_enabled = data.get("metacognition_enabled", True)
        self.thought_history = []
        for td in data.get("thought_history", []):
            try:
                style = ThinkingStyle(td.get("style", "analytical"))
            except ValueError:
                style = ThinkingStyle.ANALYTICAL
            thought = Thought(
                content=td.get("content", ""),
                style=style,
                confidence=td.get("confidence", 0.5),
                timestamp=td.get("timestamp", datetime.now(timezone.utc).isoformat()),
                id=td.get("id", ""),
                parent_id=td.get("parent_id"),
                metadata=td.get("metadata", {}),
            )
            self.thought_history.append(thought)
        self.thought_history = self.thought_history[-self.max_history:]

    def export(self) -> dict:
        return {
            "total_thoughts": len(self.thought_history),
            "recent_thoughts": [t.to_dict() for t in self.thought_history[-10:]],
        }
