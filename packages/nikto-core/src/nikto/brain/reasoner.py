"""
NiktoReasoner — NICTO's Multi-Strategy Reasoning Engine.

NICTO reasons using multiple reasoning strategies simultaneously
and selects the best answer through an internal voting system.

Five reasoning strategies:
1. Deductive - logical rules and facts
2. Inductive - pattern recognition from experience
3. Analogical - this is like that other thing
4. Causal - cause and effect reasoning
5. Creative - novel combinations and solutions
"""

import asyncio
from typing import Optional

from .models import (
    Perception, Memory, KnowledgeFact, Reasoning, 
    ReasoningResult, SynthesisResult, KnowledgeSet
)


class NiktoReasoner:
    """
    NICTO's internal reasoning engine.
    
    Uses 5 parallel reasoning strategies and combines them
    into a single best answer with confidence score.
    
    Strategies:
    - Deductive: If A then B. A is true. Therefore B.
      Used for: factual questions, code logic, math
    - Inductive: Pattern recognition from past experience.
      Used for: debugging, predicting outcomes
    - Analogical: This is like that other thing I know.
      Used for: explaining concepts, cross-domain solutions
    - Causal: What caused this? What will this cause?
      Used for: root cause analysis, impact assessment
    - Creative: Novel combinations and solutions.
      Used for: architecture design, creative requests
    """

    def __init__(self):
        """Initialize the reasoner."""
        self._strategy_weights = {
            "deductive": 0.9,
            "inductive": 0.85,
            "analogical": 0.7,
            "causal": 0.75,
            "creative": 0.6,
        }

    async def reason(
        self,
        perception: Perception,
        memories: list[Memory],
        knowledge: list[KnowledgeFact]
    ) -> Reasoning:
        """
        Run all reasoning strategies and synthesize results.
        
        Args:
            perception: Current perception
            memories: Relevant memories
            knowledge: Relevant knowledge
            
        Returns:
            Combined reasoning result
        """
        # Run all strategies in parallel
        results = await asyncio.gather(
            self._deductive_reasoning(perception, knowledge),
            self._inductive_reasoning(perception, memories),
            self._analogical_reasoning(perception, memories),
            self._causal_reasoning(perception, knowledge),
            self._creative_reasoning(perception),
        )

        # Combine reasoning chains
        combined = self._synthesize_reasoning(results)

        # Score confidence
        confidence = self._calculate_confidence(combined, knowledge, perception)

        # Build step-by-step reasoning chain
        chain = self._build_chain(results)

        # Determine if clarification is needed
        requires_clarification = confidence < 0.4 or len(combined.gaps) > 2

        return Reasoning(
            conclusion=combined.best_answer,
            confidence=confidence,
            chain=chain,
            alternatives=combined.alternatives,
            knowledge_gaps=combined.gaps,
            requires_clarification=requires_clarification,
            domain=perception.domain
        )

    async def _deductive_reasoning(
        self,
        perception: Perception,
        knowledge: list[KnowledgeFact]
    ) -> ReasoningResult:
        """
        Deductive reasoning: logical rules and facts.
        
        If A then B. A is true. Therefore B.
        Used for: factual questions, code logic, mathematics.
        
        Args:
            perception: Current perception
            knowledge: Relevant knowledge facts
            
        Returns:
            Reasoning result with conclusions
        """
        applicable_rules = []
        
        for fact in knowledge:
            if self._rule_applies(fact, perception):
                applicable_rules.append(fact)
        
        conclusions = []
        for rule in applicable_rules:
            conclusion = self._apply_rule(rule, perception)
            if conclusion:
                conclusions.append(conclusion)
        
        # Also try to deduce from perception content
        if not conclusions:
            deduced = self._deduce_from_perception(perception)
            if deduced:
                conclusions.append(deduced)
        
        return ReasoningResult(
            strategy="deductive",
            conclusions=conclusions if conclusions else [],
            confidence=0.9 if conclusions else 0.1
        )

    def _rule_applies(self, fact: KnowledgeFact, perception: Perception) -> bool:
        """Check if a knowledge rule applies to the current perception."""
        # Check domain match
        if fact.domain != perception.domain and fact.domain:
            # Partial match - may still apply
            domain_keywords = {
                "cybersecurity": ["security", "hack", "vulnerability", "exploit"],
                "programming": ["code", "function", "class", "debug", "error"],
                "ai_ml": ["model", "machine learning", "neural", "ai"],
            }
            
            domain_words = domain_keywords.get(perception.domain, [])
            fact_words = set(fact.content.lower().split())
            
            for word in domain_words:
                if word in fact_words:
                    return True
        
        # Check keyword overlap
        perception_words = set(perception.raw_input.lower().split())
        fact_words = set(fact.content.lower().split())
        
        overlap = len(perception_words & fact_words)
        return overlap >= 2

    def _apply_rule(self, fact: KnowledgeFact, perception: Perception) -> Optional[str]:
        """Apply a knowledge rule to the perception."""
        # Simple rule application based on pattern matching
        if fact.domain == perception.domain:
            # Same domain - apply the knowledge
            return fact.content
        
        return None

    def _deduce_from_perception(self, perception: Perception) -> Optional[str]:
        """Deduce information directly from perception content."""
        text = perception.raw_input.lower()
        
        # Detect programming language from code patterns
        if "def " in text or "import " in text:
            return "This appears to be a Python programming question"
        
        if "function" in text or "const " in text or "let " in text:
            return "This appears to be a JavaScript question"
        
        if "class " in text and ":" in text:
            return "This appears to be an object-oriented programming question"
        
        # Detect security context
        if any(word in text for word in ["sql", "xss", "injection", "vulnerability"]):
            return "This relates to web application security"
        
        return None

    async def _inductive_reasoning(
        self,
        perception: Perception,
        memories: list[Memory]
    ) -> ReasoningResult:
        """
        Inductive reasoning: pattern recognition from experience.
        
        Uses past similar situations to predict current situation.
        Used for: debugging, predicting outcomes, recognizing problems.
        
        Args:
            perception: Current perception
            memories: Past memories
            
        Returns:
            Reasoning result with projected conclusions
        """
        if not memories:
            return ReasoningResult(
                strategy="inductive",
                conclusions=[],
                confidence=0.1
            )
        
        # Find similar past situations
        similar_past = []
        for mem in memories:
            similarity = self._similarity_score(mem, perception)
            if similarity > 0.5:
                similar_past.append((similarity, mem))
        
        if not similar_past:
            return ReasoningResult(
                strategy="inductive",
                conclusions=[],
                confidence=0.1
            )
        
        # Sort by similarity
        similar_past.sort(key=lambda x: x[0], reverse=True)
        
        # Extract patterns from similar experiences
        patterns = self._extract_patterns(similar_past)
        
        # Project patterns to current situation
        projected = self._project_patterns(patterns, perception)
        
        return ReasoningResult(
            strategy="inductive",
            conclusions=projected if projected else [],
            confidence=min(0.85, len(similar_past) * 0.15)
        )

    def _similarity_score(self, memory: Memory, perception: Perception) -> float:
        """Calculate similarity between memory and perception."""
        memory_words = set(memory.content.lower().split())
        perception_words = set(perception.raw_input.lower().split())
        
        # Word overlap
        overlap = len(memory_words & perception_words)
        
        # Domain match bonus
        domain_bonus = 0.2 if memory.domain == perception.domain else 0
        
        # Calculate score
        if not perception_words:
            return 0.0
        
        base_score = overlap / len(perception_words)
        
        # Also consider word overlap relative to memory size
        if memory_words:
            recall_score = overlap / len(memory_words)
            base_score = (base_score + recall_score) / 2
        
        return min(1.0, base_score + domain_bonus)

    def _extract_patterns(self, similar_memories: list) -> list[str]:
        """Extract common patterns from similar memories."""
        patterns = []
        
        for _, mem in similar_memories:
            # Extract outcome pattern
            if "->" in mem.content:
                parts = mem.content.split("->")
                if len(parts) == 2:
                    outcome = parts[1].strip()
                    if outcome and len(outcome) < 100:
                        patterns.append(outcome)
        
        return patterns[:5]  # Limit to top patterns

    def _project_patterns(
        self,
        patterns: list[str],
        perception: Perception
    ) -> list[str]:
        """Project extracted patterns to current situation."""
        projected = []
        
        for pattern in patterns:
            # Check if pattern is relevant to current perception
            pattern_words = set(pattern.lower().split())
            perception_words = set(perception.raw_input.lower().split())
            
            overlap = len(pattern_words & perception_words)
            
            if overlap > 0:
                projected.append(pattern)
        
        return projected

    async def _analogical_reasoning(
        self,
        perception: Perception,
        memories: list[Memory]
    ) -> ReasoningResult:
        """
        Analogical reasoning: this is like that.
        
        Uses knowledge from one domain to solve problems in another.
        Used for: explaining concepts, cross-domain problem solving.
        
        Args:
            perception: Current perception
            memories: Past memories for analogies
            
        Returns:
            Reasoning result with mapped analogies
        """
        analogies = self._find_analogies(perception, memories)
        
        if not analogies:
            return ReasoningResult(
                strategy="analogical",
                conclusions=[],
                confidence=0.0
            )
        
        # Map the best analogy to the current problem
        mapped = self._map_analogy_to_problem(analogies[0], perception)
        
        return ReasoningResult(
            strategy="analogical",
            conclusions=[mapped] if mapped else [],
            confidence=0.7
        )

    def _find_analogies(
        self,
        perception: Perception,
        memories: list[Memory]
    ) -> list[tuple[float, str]]:
        """Find analogies from memories that relate to the current problem."""
        analogies = []
        
        # Common analogy patterns
        analogy_markers = [
            "like", "similar to", " analogous to", "same as",
            "reminds me of", "equivalent to", "like when"
        ]
        
        for mem in memories:
            mem_lower = mem.content.lower()
            
            # Check if memory contains analogy language
            for marker in analogy_markers:
                if marker in mem_lower:
                    # Extract the analogy
                    idx = mem_lower.index(marker)
                    analogy = mem.content[idx:idx+100]
                    similarity = self._similarity_score(mem, perception)
                    analogies.append((similarity, analogy))
                    break
        
        analogies.sort(key=lambda x: x[0], reverse=True)
        return analogies[:3]

    def _map_analogy_to_problem(
        self,
        analogy: tuple[float, str],
        perception: Perception
    ) -> Optional[str]:
        """Map an analogy to the current problem."""
        similarity, analogy_text = analogy
        
        if similarity < 0.4:
            return None
        
        # Format the analogy for use
        return f"Similar to: {analogy_text[:80]}..."

    async def _causal_reasoning(
        self,
        perception: Perception,
        knowledge: list[KnowledgeFact]
    ) -> ReasoningResult:
        """
        Causal reasoning: cause and effect.
        
        Analyzes what caused the current situation and what
        effects the response might have.
        Used for: debugging, root cause analysis, impact assessment.
        
        Args:
            perception: Current perception
            knowledge: Relevant knowledge
            
        Returns:
            Reasoning result with causes and effects
        """
        causes = self._find_causes(perception, knowledge)
        effects = self._predict_effects(perception, knowledge)
        
        conclusions = causes + effects
        
        return ReasoningResult(
            strategy="causal",
            conclusions=conclusions,
            confidence=0.75 if causes else 0.3
        )

    def _find_causes(
        self,
        perception: Perception,
        knowledge: list[KnowledgeFact]
    ) -> list[str]:
        """Find potential causes of the current situation."""
        causes = []
        
        # From perception analysis
        text = perception.raw_input.lower()
        
        # Error/debugging context
        if perception.intent.value == "debug":
            if "error" in text:
                causes.append("Error likely caused by misconfiguration or unexpected input")
            if "crash" in text:
                causes.append("Crash may be due to memory issue or infinite loop")
            if "not working" in text:
                causes.append("Not working could indicate logic error or missing dependency")
        
        # From knowledge
        for fact in knowledge:
            if "cause" in fact.content.lower() or "due to" in fact.content.lower():
                causes.append(fact.content[:80])
        
        return causes[:3]

    def _predict_effects(
        self,
        perception: Perception,
        knowledge: list[KnowledgeFact]
    ) -> list[str]:
        """Predict effects of responding in this way."""
        effects = []
        
        # Predict based on intent
        if perception.intent.value == "build":
            effects.append("Building/coding will produce functional implementation")
        elif perception.intent.value == "debug":
            effects.append("Debugging guidance should resolve the issue")
        elif perception.intent.value == "learn":
            effects.append("Learning response should increase understanding")
        
        return effects

    async def _creative_reasoning(
        self,
        perception: Perception
    ) -> ReasoningResult:
        """
        Creative reasoning: novel combinations and solutions.
        
        Generates novel approaches when standard solutions don't fit.
        Used for: creative requests, architecture design.
        
        Args:
            perception: Current perception
            
        Returns:
            Reasoning result with novel approaches
        """
        novel_approaches = self._generate_novel_approaches(perception)
        
        return ReasoningResult(
            strategy="creative",
            conclusions=novel_approaches,
            confidence=0.6
        )

    def _generate_novel_approaches(self, perception: Perception) -> list[str]:
        """Generate novel approaches to the problem."""
        approaches = []
        
        # For creative/generate intents, suggest alternative approaches
        if perception.intent.value in ["generate", "build"]:
            approaches.append("Consider using a framework or library to accelerate development")
            approaches.append("Break the problem into smaller, testable components")
        
        # For debugging, suggest alternative debugging approaches
        if perception.intent.value == "debug":
            approaches.append("Try rubber duck debugging: explain the problem step by step")
            approaches.append("Isolate the issue by creating a minimal reproduction case")
        
        # For learning, suggest alternative learning methods
        if perception.intent.value == "learn":
            approaches.append("Consider learning through practical examples rather than theory")
            approaches.append("Build a small project to reinforce the concept")
        
        return approaches[:3]

    def _synthesize_reasoning(
        self,
        results: list[ReasoningResult]
    ) -> SynthesisResult:
        """
        Combine all reasoning strategies into one best answer.
        
        Higher confidence strategies get more weight in the synthesis.
        
        Args:
            results: List of reasoning results from each strategy
            
        Returns:
            Synthesized result with best answer and alternatives
        """
        weighted_conclusions = []
        
        for result in results:
            weight = self._strategy_weights.get(result.strategy, 0.5)
            
            for conclusion in result.conclusions:
                weighted_conclusions.append({
                    "conclusion": conclusion,
                    "weight": weight * result.confidence,
                    "strategy": result.strategy
                })
        
        if not weighted_conclusions:
            return SynthesisResult(
                best_answer="",
                alternatives=[],
                gaps=["Insufficient knowledge to answer"]
            )
        
        # Sort by weight
        weighted_conclusions.sort(key=lambda x: x["weight"], reverse=True)
        
        # Best answer
        best = weighted_conclusions[0]["conclusion"]
        
        # Alternatives (2nd and 3rd)
        alternatives = [
            c["conclusion"] for c in weighted_conclusions[1:3]
            if c["conclusion"] != best
        ]
        
        # Identify gaps
        gaps = self._identify_knowledge_gaps(results)
        
        return SynthesisResult(
            best_answer=best,
            alternatives=alternatives,
            gaps=gaps
        )

    def _identify_knowledge_gaps(
        self,
        results: list[ReasoningResult]
    ) -> list[str]:
        """Identify areas where NICTO lacks knowledge."""
        gaps = []
        
        # Check each strategy for lack of conclusions
        for result in results:
            if not result.conclusions and result.confidence < 0.3:
                gaps.append(f"Limited {result.strategy} reasoning for this topic")
        
        return gaps[:5]

    def _calculate_confidence(
        self,
        synthesis: SynthesisResult,
        knowledge: list[KnowledgeFact],
        perception: Perception
    ) -> float:
        """
        Calculate overall confidence score (0.0 to 1.0).
        
        Based on: knowledge coverage, reasoning agreement,
        topic familiarity, gap count.
        
        Args:
            synthesis: The synthesized result
            knowledge: Relevant knowledge
            perception: Current perception
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Start with base confidence
        confidence = 0.5
        
        # Boost for sufficient knowledge
        if len(knowledge) >= 5:
            confidence += 0.2
        elif len(knowledge) >= 2:
            confidence += 0.1
        
        # Boost for no gaps
        if not synthesis.gaps:
            confidence += 0.15
        else:
            confidence -= len(synthesis.gaps) * 0.1
        
        # Boost for strong conclusion
        if synthesis.best_answer and len(synthesis.best_answer) > 20:
            confidence += 0.1
        
        # Boost for alternatives (shows thorough reasoning)
        if synthesis.alternatives:
            confidence += 0.05
        
        # Check domain familiarity
        domain_confidences = {
            "cybersecurity": 0.95,
            "programming": 0.95,
            "ai_ml": 0.90,
            "mathematics": 0.85,
            "network_engineering": 0.90,
            "cryptography": 0.90,
            "game_development": 0.85,
            "system_administration": 0.90,
            "cloud_infrastructure": 0.80,
            "data_science": 0.85,
            "electronics_iot": 0.75,
        }
        
        domain_familiarity = domain_confidences.get(perception.domain, 0.6)
        confidence = confidence * 0.7 + domain_familiarity * 0.3
        
        return max(0.0, min(1.0, confidence))

    def _build_chain(self, results: list[ReasoningResult]) -> list[str]:
        """Build a step-by-step reasoning chain."""
        chain = []
        
        for result in results:
            if result.conclusions:
                chain.append(f"[{result.strategy.upper()}] {result.conclusions[0]}")
        
        return chain