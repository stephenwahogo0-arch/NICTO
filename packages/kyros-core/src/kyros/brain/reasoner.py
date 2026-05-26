import json
import random
import math
from datetime import datetime, timezone
from typing import Optional
from kyros.brain.models import ThinkingStyle, Thought


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

    def _decompose(self, prompt: str) -> str:
        steps = [
            f"Analyzing: {prompt}",
            "Identifying key variables and relationships",
            "Evaluating cause and effect",
            f"Conclusion: Based on systematic analysis, {self._generate_conclusion(prompt)}",
        ]
        return " | ".join(steps)

    def _logical_deduction(self, prompt: str, premises: list) -> str:
        if not premises:
            return f"From first principles: {prompt} → therefore, {self._generate_conclusion(prompt)}"
        chain = " → ".join(premises)
        return f"Premises: {chain} → Conclusion for '{prompt}': {self._generate_conclusion(prompt)}"

    def _induce_generalization(self, prompt: str, observations: list) -> str:
        if not observations:
            return f"From observed patterns in '{prompt}': {self._generate_conclusion(prompt)} (generalization)"
        obs = "; ".join(observations[:3])
        return f"Observed: {obs} → Pattern: {prompt} → Generalized: {self._generate_conclusion(prompt)}"

    def _best_explanation(self, prompt: str, observations: list) -> str:
        if not observations:
            return f"Best explanation for '{prompt}': {self._generate_conclusion(prompt)}"
        obs = "; ".join(observations[:2])
        return f"Given: {obs} → Best explanation: {self._generate_conclusion(prompt)}"

    def _analogical_reasoning(self, prompt: str, source: str) -> str:
        return f"Using analogy from '{source}': {prompt} → Parallel: {self._generate_conclusion(prompt)}"

    def _critical_analysis(self, prompt: str) -> str:
        return (
            f"Critically examining: {prompt} | "
            f"Assumptions: questioning underlying premises | "
            f"Counterarguments: {self._generate_conclusion('counterpoint to ' + prompt)} | "
            f"Refined view: {self._generate_conclusion(prompt)} (after critical assessment)"
        )

    def _creative_synthesis(self, prompt: str, constraints: list) -> str:
        constraint_note = f" within constraints: {'; '.join(constraints)}" if constraints else ""
        return f"Creative synthesis for '{prompt}'{constraint_note}: {self._generate_conclusion(prompt)} (novel combination)"

    def _intuitive_leap(self, prompt: str, context: dict) -> str:
        return f"Intuitive insight on '{prompt}': {self._generate_conclusion(prompt)} (rapid pattern match)"

    def _generate_conclusion(self, prompt: str) -> str:
        conclusions = [
            f"a systematic approach reveals optimal solution paths for '{prompt[:50]}'",
            f"multiple evidence streams converge on a coherent understanding of '{prompt[:50]}'",
            f"integrating perspectives yields a nuanced resolution for '{prompt[:50]}'",
            f"the underlying structure of '{prompt[:50]}' becomes clear through analysis",
            f"a balanced evaluation suggests actionable insights for '{prompt[:50]}'",
        ]
        return random.choice(conclusions)

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
