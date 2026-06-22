"""
Math Brain for NIKTO
Specialized brain for solving mathematical and physics problems using
integrated knowledge, reasoning, and learning components.
"""

from typing import Dict, Any, Optional, List
from nikto.brain.core import NiktoBrain
from nikto.brain.reasoner import NiktoReasoner
from nikto.brain.memory import NiktoLongTermMemory
from nikto.brain.learner import NiktoLearner
from nikto.brain.language import NiktoLanguageEngine
from nikto.brain.knowledge import NiktoKnowledgeCore
from nikto.knowledge.loader import search_knowledge


class MathBrain:
    """
    A brain dedicated to mathematical and scientific problem solving.
    Combines knowledge retrieval, logical reasoning, and learning to
    tackle math/physics queries.
    """

    def __init__(self):
        self.brain = NiktoBrain()
        self.reasoner = NiktoReasoner()
        self.knowledge = NiktoKnowledgeCore()
        self.memory = NiktoLongTermMemory()
        self.learner = NiktoLearner()
        self.language = NiktoLanguageEngine()
        self._initialized = False

    async def awaken(self):
        """Awaken underlying brain components."""
        await self.brain.awaken()
        self._initialized = True

    async def solve_problem(self, problem: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Solve a mathematical or physics problem.
        Returns a dictionary with solution steps, final answer, and confidence.
        """
        if not self._initialized:
            await self.awaken()

        # 1. Language understanding
        lang_info = self.language.understand(problem)
        
        # 2. Retrieve relevant knowledge
        knowledge_results = search_knowledge(problem)
        
        # 3. Reason about the problem
        reasoning_result = self.reasoner.reason(
            problem,
            {
                "knowledge": knowledge_results,
                "language": lang_info,
                "context": context or {}
            }
        )
        
        # Extract content and confidence from Thought object
        solution_content = reasoning_result.content if hasattr(reasoning_result, 'content') else str(reasoning_result)
        reasoning_confidence = reasoning_result.confidence if hasattr(reasoning_result, 'confidence') else 0.5
        
        # 4. Store in memory for future reference
        self.memory.store(
            content=f"Problem: {problem}\nSolution: {solution_content}",
            tags=["math", "solution"],
            importance=0.9
        )
        
        # 5. Learn from this interaction
        self.learner.learn(
            topic=f"Math problem solution: {hash(problem) % 10000}",
            content=f"Problem: {problem}\nSolution: {solution_content}",
            source="math_problem_solving"
        )
        
        return {
            "problem": problem,
            "language_analysis": lang_info,
            "knowledge_sources": [k.get('statement', '') if isinstance(k, dict) else str(k) for k in knowledge_results],
            "reasoning_steps": reasoning_result.to_dict() if hasattr(reasoning_result, 'to_dict') else {"content": solution_content, "confidence": reasoning_confidence},
            "solution": solution_content,
            "confidence": reasoning_confidence,
            "stored_in_memory": True
        }

    def get_status(self) -> Dict[str, Any]:
        """Get status of the math brain and its components."""
        return {
            "initialized": self._initialized,
            "brain": self.brain.get_status() if self._initialized else None,
            "knowledge_facts": len(self.knowledge.facts),
            "knowledge_concepts": len(self.knowledge.concepts),
            "knowledge_beliefs": len(self.knowledge.beliefs),
            "memory_fragments": len(self.memory.fragments),
            "lessons_learned": len(self.learner.lesson_store)
        }