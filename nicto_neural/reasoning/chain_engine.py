import re
import hashlib
from typing import Any, Dict, List, Optional, Tuple


class NeuralConfig:
    def __init__(self, d_model: int = 512, device: str = "cpu"):
        self.d_model = d_model
        self.device = device


class ChainEngine:
    def __init__(self, config: Optional[NeuralConfig] = None):
        self.config = config if config is not None else NeuralConfig()
        self._chains: Dict[str, List[str]] = {}
        self._templates = {
            "analytical": [
                "Analyze the problem: {task}",
                "Identify key components and constraints",
                "Break down into smaller sub-problems",
                "Solve each sub-problem systematically",
                "Combine solutions into final answer: {task}",
            ],
            "deductive": [
                "Given: {task}",
                "Identify known facts and premises",
                "Apply logical rules to derive new information",
                "Chain deductions toward conclusion",
                "Therefore, the answer is derived from {task}",
            ],
            "stepwise": [
                "Step 1: Understand what {task} requires",
                "Step 2: Gather relevant information for {task}",
                "Step 3: Process and analyze the information",
                "Step 4: Formulate solution for {task}",
                "Step 5: Verify the solution addresses {task}",
            ],
            "creative": [
                "Consider {task} from multiple perspectives",
                "Generate diverse approaches to {task}",
                "Evaluate each approach for feasibility",
                "Synthesize the best elements",
                "Produce innovative solution for {task}",
            ],
        }
        self._default_template = self._templates["stepwise"]

    def _chain_id(self, task: str) -> str:
        return hashlib.md5(task.encode()).hexdigest()[:16]

    def build_chain(self, task: str, max_steps: int = 10) -> List[str]:
        cid = self._chain_id(task)
        if cid in self._chains:
            return self._chains[cid]

        task_lower = task.lower()
        if any(w in task_lower for w in ["why", "because", "therefore", "imply", "deduce", "logical", "proof"]):
            template = self._templates["deductive"]
        elif any(w in task_lower for w in ["create", "design", "invent", "novel", "imagine", "creative", "brainstorm"]):
            template = self._templates["creative"]
        elif any(w in task_lower for w in ["analyze", "compare", "evaluate", "examine", "investigate"]):
            template = self._templates["analytical"]
        else:
            template = self._templates["stepwise"]

        chain = []
        for step in template[:max_steps]:
            filled = step.format(task=task)
            chain.append(filled)

        if max_steps > len(template):
            for i in range(len(template), max_steps):
                chain.append(f"Reasoning step {i + 1}: iterating on {task}")

        self._chains[cid] = chain
        return chain

    def add_step(self, chain: List[str], step: str) -> List[str]:
        chain.append(step)
        return chain

    def backtrack(self, chain: List[str], to_step: int) -> List[str]:
        if to_step < 0:
            return []
        if to_step >= len(chain):
            return chain[:]
        return chain[:to_step + 1]

    def verify_chain_consistency(self, chain: List[str]) -> Tuple[bool, int]:
        if len(chain) < 2:
            return (True, -1)

        contradiction_pairs = [
            (r"\bnot\b.*\b(is|are|was|were|have|has|had|will|shall|can|could|would|should)\b", r"\b\1\b.*\b(not)\b"),
        ]

        affirmative_negative = [
            (r"\b(is|are|was|were|does|do|has|have|will|shall|can|could|would|should)\s+not\b", True),
            (r"\b(is|are|was|were|does|do|has|have|will|shall|can|could|would|should)\s+\w+\b", False),
        ]

        negation_patterns = [
            r"\bnot\b", r"\bnever\b", r"\bnone\b", r"\bnothing\b",
            r"\bno one\b", r"\bnowhere\b", r"\bneither\b", r"\bnor\b",
            r"\bwithout\b", r"\bexcept\b", r"\bexclude\b", r"\bfalse\b",
        ]
        affirmation_patterns = [
            r"\balways\b", r"\ball\b", r"\bevery\b", r"\beveryone\b",
            r"\beverything\b", r"\bpositive\b", r"\btrue\b", r"\byes\b",
            r"\binclude\b", r"\bcontain\b", r"\bsupport\b",
        ]

        for i in range(len(chain) - 1):
            for j in range(i + 1, min(len(chain), i + 5)):
                step_i = chain[i].lower()
                step_j = chain[j].lower()

                has_negation_i = sum(1 for p in negation_patterns if re.search(p, step_i))
                has_affirmation_j = sum(1 for p in affirmation_patterns if re.search(p, step_j))

                has_negation_j = sum(1 for p in negation_patterns if re.search(p, step_j))
                has_affirmation_i = sum(1 for p in affirmation_patterns if re.search(p, step_i))

                if has_negation_i > 0 and has_affirmation_j > 0:
                    common = self._extract_core_topic(step_i) & self._extract_core_topic(step_j)
                    if len(common) >= 2:
                        return (False, j)

                if has_negation_j > 0 and has_affirmation_i > 0:
                    common = self._extract_core_topic(step_i) & self._extract_core_topic(step_j)
                    if len(common) >= 2:
                        return (False, i)

                for pat_a, _ in contradiction_pairs:
                    try:
                        if re.search(pat_a, step_i, re.IGNORECASE) and re.search(pat_a, step_j, re.IGNORECASE):
                            return (False, j)
                    except re.error:
                        pass

                shared_words = self._extract_core_topic(step_i) & self._extract_core_topic(step_j)
                specific_nouns = {w for w in shared_words if len(w) > 4}

                if len(specific_nouns) >= 2:
                    step_i_has_not = bool(re.search(r'\bnot\b', step_i))
                    step_j_has_not = bool(re.search(r'\bnot\b', step_j))
                    if step_i_has_not != step_j_has_not:
                        return (False, j)

        return (True, -1)

    def _extract_core_topic(self, text: str) -> set:
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "shall",
            "should", "may", "might", "must", "can", "could", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "into", "through",
            "during", "before", "after", "above", "below", "between", "out",
            "off", "over", "under", "again", "further", "then", "once", "here",
            "there", "when", "where", "why", "how", "all", "each", "every",
            "both", "few", "more", "most", "other", "some", "such", "no", "nor",
            "not", "only", "own", "same", "so", "than", "too", "very", "just",
            "because", "and", "but", "or", "if", "while", "this", "that", "these",
            "those", "it", "its", "step", "consider", "identify", "apply",
        }
        words = set(re.findall(r'\b[a-zA-Z]\w+\b', text.lower()))
        return words - stop_words

    def final_answer(self, chain: List[str]) -> str:
        if not chain:
            return ""
        for step in reversed(chain):
            if re.search(r'\b(answer|result|conclusion|solution|final|therefore|thus|hence|so|output)\b', step.lower()):
                return step
        return chain[-1]
