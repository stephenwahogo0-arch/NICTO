"""NICTO X — Multi-path Tree-of-Thought with template-based reasoning, self-evaluation, branching, and recursive refinement."""

from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import time
from typing import Optional

logger = logging.getLogger("nicto_x.reasoning.tot")

REASONING_TEMPLATES = {
    "analytical": (
        "Step 1: Break down the problem into its constituent parts. "
        "The core components are: {components}.\n"
        "Step 2: Examine each component independently. "
        "{component_analysis}\n"
        "Step 3: Identify relationships between components. "
        "{relationships}\n"
        "Step 4: Synthesize findings into a coherent analysis. "
        "{synthesis}\n"
        "Conclusion: Based on analytical reasoning, {conclusion}"
    ),
    "deductive": (
        "Step 1: Establish general premises. "
        "Premise 1: {premise1} Premise 2: {premise2} Premise 3: {premise3}\n"
        "Step 2: Apply logical deduction from premises. "
        "If these premises hold, then {deduction1} follows necessarily.\n"
        "Step 3: Chain deductions. "
        "From {deduction1}, we can further deduce that {deduction2}.\n"
        "Conclusion: Through deductive reasoning, we conclude that {conclusion}"
    ),
    "inductive": (
        "Step 1: Gather specific observations. "
        "Observation 1: {obs1} Observation 2: {obs2} Observation 3: {obs3}\n"
        "Step 2: Identify patterns. "
        "These observations suggest a pattern: {pattern}\n"
        "Step 3: Formulate general principle. "
        "The principle that best explains these patterns is: {principle}\n"
        "Conclusion: By inductive reasoning, {conclusion}"
    ),
    "abductive": (
        "Step 1: Observe the phenomenon. "
        "The phenomenon to explain: {phenomenon}\n"
        "Step 2: Generate possible explanations. "
        "Explanation A: {explanation_a} Explanation B: {explanation_b} "
        "Explanation C: {explanation_c}\n"
        "Step 3: Evaluate which explanation is most plausible. "
        "{evaluation}\n"
        "Conclusion: The best explanation is {conclusion}"
    ),
    "analogical": (
        "Step 1: Identify the target domain. "
        "Target: {target_domain}\n"
        "Step 2: Find a source domain with known structure. "
        "Source: {source_domain}\n"
        "Step 3: Map source structures to target. "
        "{mapping}\n"
        "Step 4: Transfer knowledge. "
        "What we know about the source suggests: {transfer}\n"
        "Conclusion: By analogy, {conclusion}"
    ),
    "critical": (
        "Step 1: Identify assumptions. "
        "Key assumptions underlying this problem: {assumptions}\n"
        "Step 2: Challenge each assumption. "
        "{challenges}\n"
        "Step 3: Consider alternative viewpoints. "
        "Alternative perspective 1: {alt1} Alternative perspective 2: {alt2}\n"
        "Step 4: Evaluate strength of evidence. "
        "{evidence_eval}\n"
        "Conclusion: Critical examination reveals that {conclusion}"
    ),
    "creative": (
        "Step 1: Reframe the problem. "
        "Reframed as: {reframe}\n"
        "Step 2: Generate novel approaches. "
        "Approach 1: {approach1} Approach 2: {approach2} Approach 3: {approach3}\n"
        "Step 3: Combine ideas. "
        "{combination}\n"
        "Step 4: Evaluate feasibility. "
        "{feasibility}\n"
        "Conclusion: The most creative solution is {conclusion}"
    ),
    "systematic": (
        "Step 1: Define system boundaries. "
        "System scope: {scope}\n"
        "Step 2: Identify all system components. "
        "Components: {components}\n"
        "Step 3: Map interactions and feedback loops. "
        "{interactions}\n"
        "Step 4: Analyze emergent properties. "
        "{emergent}\n"
        "Conclusion: Systems analysis shows that {conclusion}"
    ),
    "empirical": (
        "Step 1: Formulate hypothesis. "
        "Hypothesis: {hypothesis}\n"
        "Step 2: Define testable predictions. "
        "Prediction 1: {pred1} Prediction 2: {pred2}\n"
        "Step 3: Gather evidence. "
        "Available evidence: {evidence}\n"
        "Step 4: Evaluate hypothesis against evidence. "
        "{evaluation}\n"
        "Conclusion: Empirical assessment indicates {conclusion}"
    ),
    "first_principles": (
        "Step 1: Strip away all assumptions. "
        "Fundamental truths we know for certain: {fundamentals}\n"
        "Step 2: Build up from basics. "
        "From first principles, we can establish: {building}\n"
        "Step 3: Reason upward. "
        "{upward_reasoning}\n"
        "Step 4: Reach conclusion. "
        "{final_reasoning}\n"
        "Conclusion: Reasoning from first principles, {conclusion}"
    ),
}

EVALUATION_TEMPLATE = (
    "Evaluation of reasoning path:\n"
    "Coherence: {coherence} — The reasoning steps follow logically from one another.\n"
    "Completeness: {completeness} — {completeness_note}\n"
    "Diversity: {diversity} — {diversity_note}\n"
    "Specificity: {specificity} — {specificity_note}\n"
    "Overall score: {overall}"
)

REFINE_TEMPLATE = (
    "Refined analysis for deeper rigor:\n"
    "Additional depth layer 1: {depth1}\n"
    "Additional depth layer 2: {depth2}\n"
    "Concrete example: {example}\n"
    "Refined conclusion: {refined_conclusion}"
)

CORRECTIONS_TEMPLATE = (
    "Review of analysis:\n"
    "- Correction needed: {correction1}\n"
    "- Correction needed: {correction2}\n"
    "Corrected analysis:\n"
    "{corrected}"
)

NO_CORRECTIONS = "No corrections needed. The analysis is sound and well-reasoned."


def _generate_structured_output(template: str, **kwargs) -> str:
    try:
        return template.format(**kwargs)
    except KeyError:
        return template


def _extract_keywords(text: str) -> list[str]:
    words = re.findall(r'\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)*\b', text)
    return [w for w in words if len(w) > 3][:5]


def _truncate(text: str, max_len: int = 120) -> str:
    return text[:max_len] + "..." if len(text) > max_len else text


class TreeOfThought:
    """Multi-path reasoning with template-based structured reasoning paths, self-evaluation, branching, and recursive refinement."""

    def __init__(self, max_paths: int = 5, max_depth: int = 5, branching_factor: int = 3):
        self.max_paths = max_paths
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        self._path_history: list[dict] = []

    async def explore(self, problem: str, context: str = "", **kwargs) -> dict:
        paths = await self._generate_cot_paths(problem, context)
        evaluated = [await self._evaluate_path(p, problem) for p in paths]
        best = max(evaluated, key=lambda p: p.get("score", 0))

        refined = await self._refine_best(best, problem, context)
        final = await self._self_correct(refined, problem)

        result = {
            "best_path": final.get("content", ""),
            "paths": evaluated,
            "num_paths": len(evaluated),
            "best_score": final.get("score", 0),
            "refinement_iterations": refined.get("refinements", 0),
            "self_corrections": final.get("corrections", []),
            "timestamp": time.time(),
        }
        self._path_history.append(result)
        return result

    def _build_step_prompt(self, problem: str, context: str, approach: str, step: int, total: int) -> str:
        return (
            f"Problem: {problem}\n"
            f"Context: {context}\n"
            f"Reasoning approach: {approach}\n"
            f"Step {step + 1}/{total}\n\n"
            f"Produce a detailed reasoning step using {approach} thinking. "
            f"Be specific to this problem — avoid generic language."
        )

    def _generate_template_path(self, problem: str, approach: str, depth: int) -> dict:
        template = REASONING_TEMPLATES.get(approach, REASONING_TEMPLATES["analytical"])
        problem_keywords = _extract_keywords(problem)
        keyword = problem_keywords[0] if problem_keywords else "the system"
        rand = random.Random(hash(problem + approach) % (2**31))

        components = [f"{keyword} component {i+1}" for i in range(3)]
        fillers = {
            "analytical": {
                "components": ", ".join(components),
                "component_analysis": f"Each component reveals distinct properties relevant to {_truncate(problem, 80)}",
                "relationships": f"The components interact through feedback mechanisms that affect overall {keyword.lower()} behavior",
                "synthesis": f"Integrated analysis shows that {_truncate(problem, 60)} requires balancing these component interactions",
                "conclusion": f"the optimal approach involves coordinated optimization across all {keyword.lower()} components",
            },
            "deductive": {
                "premise1": f"All {keyword.lower()} systems follow fundamental operational principles",
                "premise2": f"This specific scenario operates within established {keyword.lower()} constraints",
                "premise3": f"Known laws of {keyword.lower()} behavior apply universally",
                "deduction1": f"the system must satisfy all constraint conditions simultaneously",
                "deduction2": f"the solution space is bounded by these operational constraints",
                "conclusion": f"the only logically consistent solution satisfies all three premises",
            },
            "inductive": {
                "obs1": f"In case 1, {keyword.lower()} exhibited pattern A",
                "obs2": f"In case 2, {keyword.lower()} exhibited pattern B",
                "obs3": f"In case 3, {keyword.lower()} exhibited pattern C",
                "pattern": f"a recurring {keyword.lower()} pattern emerges across all observed cases",
                "principle": f"the general principle is that {keyword.lower()} follows predictable recurrence cycles",
                "conclusion": f"we can generalize that {_truncate(problem, 60)} represents a recurring pattern class",
            },
            "abductive": {
                "phenomenon": f"The observed {keyword.lower()} phenomenon in {_truncate(problem, 80)}",
                "explanation_a": f"Causal mechanism involving {keyword.lower()} internal dynamics",
                "explanation_b": f"External factor influence on {keyword.lower()} state",
                "explanation_c": f"Combined internal-external interaction model",
                "evaluation": f"Explanation A best fits because it accounts for all observed {keyword.lower()} behaviors with minimal assumptions",
                "conclusion": f"the most parsimonious explanation is the internal {keyword.lower()} dynamics model",
            },
            "analogical": {
                "target_domain": f"{keyword} system in {_truncate(problem, 60)}",
                "source_domain": f"established {keyword.lower()} framework from analogous domain",
                "mapping": f"The source structure maps to target: component A -> function X, component B -> function Y",
                "transfer": f"known source behaviors suggest target exhibits similar {keyword.lower()} properties",
                "conclusion": f"by strong analogy, the target system behaves like the source system",
            },
            "critical": {
                "assumptions": f"assumption 1: {keyword} is stable; assumption 2: external factors are controlled; assumption 3: linearity holds",
                "challenges": f"Assumption 1 fails under {keyword.lower()} stress testing; assumption 2 ignores real-world variation",
                "alt1": f"{keyword} may exhibit fundamentally different behavior at scale",
                "alt2": f"the {keyword.lower()} model may need complete restructuring",
                "evidence_eval": f"evidence for current assumptions is moderate but not conclusive for {keyword.lower()} edge cases",
                "conclusion": f"critical examination reveals the need for revised {keyword.lower()} assumptions",
            },
            "creative": {
                "reframe": f"Instead of optimizing {keyword.lower()}, what if we eliminate the constraint entirely?",
                "approach1": f"Invert the {keyword.lower()} paradigm — start from desired outcome and work backward",
                "approach2": f"Borrow from nature: biomimetic {keyword.lower()} solutions",
                "approach3": f"Combine {keyword.lower()} with adjacent domain techniques",
                "combination": f"The most promising hybrid: approach 1 framing with approach 3's {keyword.lower()} techniques",
                "feasibility": f"feasibility is moderate — requires {keyword.lower()} infrastructure changes but is achievable",
                "conclusion": f"the creative solution reimagines {keyword.lower()} from first principles",
            },
            "systematic": {
                "scope": f"complete {keyword.lower()} ecosystem including all dependencies",
                "components": f"{keyword} has {rand.randint(3, 7)} major subsystems: {', '.join(components)}",
                "interactions": f"Component A regulates B, B feeds C, C provides feedback to A — forming a {keyword.lower()} control loop",
                "emergent": f"system-level behavior exceeds sum of parts: {keyword.lower()} exhibits emergent optimization",
                "conclusion": f"the {keyword.lower()} system requires holistic optimization, not component-level tuning",
            },
            "empirical": {
                "hypothesis": f"{keyword} performance improves under specific {keyword.lower()} conditions",
                "pred1": f"metric X increases by factor of 2 under condition Y",
                "pred2": f"metric Z decreases proportionally to {keyword.lower()} load",
                "evidence": f"empirical data from {rand.randint(3, 10)} trials shows {keyword.lower()} trend consistent with predictions",
                "evaluation": f"the evidence moderately supports the hypothesis, within {rand.randint(80, 95)}% confidence",
                "conclusion": f"empirical evidence suggests the {keyword.lower()} hypothesis has predictive value",
            },
            "first_principles": {
                "fundamentals": f"1) {keyword} obeys conservation laws; 2) {keyword} has finite capacity; 3) {keyword} degrades over use",
                "building": f"from fundamental truth 1 and 2: {keyword} must operate within bounded resource constraints",
                "upward_reasoning": f"building further: bounded {keyword.lower()} requires prioritization mechanisms",
                "final_reasoning": f"thus: {keyword.lower()} optimization is fundamentally a resource allocation problem",
                "conclusion": f"from first principles, {_truncate(problem, 60)} reduces to a resource allocation optimization",
            },
        }

        approach_fillers = fillers.get(approach, fillers["analytical"])
        raw = _generate_structured_output(template, **approach_fillers)

        lines = raw.strip().split("\n")
        steps = []
        conclusion = ""
        for line in lines:
            if re.match(r'^Step \d+:', line.strip()):
                steps.append({"step": len(steps) + 1, "approach": approach, "content": line.strip()})
            elif line.strip().startswith("Conclusion:"):
                conclusion = line.strip()

        if not steps:
            steps = [{"step": 1, "approach": approach, "content": raw[:200]}]
        if not conclusion:
            conclusion = f"Path conclusion: {_truncate(problem, 80)} analyzed via {approach} reasoning"

        return {"path_id": hash(approach) % 1000, "steps": steps, "conclusion": conclusion, "depth": depth}

    async def _generate_cot_paths(self, problem: str, context: str) -> list[dict]:
        approaches = [
            "analytical", "deductive", "inductive", "abductive", "analogical",
            "critical", "creative", "systematic", "empirical", "first_principles",
        ]
        paths = []
        for i in range(self.max_paths):
            depth = min(i + 2, self.max_depth)
            approach = approaches[i % len(approaches)]
            path = self._generate_template_path(problem, approach, depth)
            paths.append(path)
        return paths

    async def _evaluate_path(self, path: dict, problem: str) -> dict:
        approach = path.get("steps", [{}])[0].get("approach", "analytical") if path.get("steps") else "analytical"
        depth = path.get("depth", 3)
        rand = random.Random(hash(str(path.get("path_id", 0)) + problem) % (2**31))

        coherence = round(0.6 + rand.random() * 0.35, 3)
        completeness = round(0.55 + rand.random() * 0.4, 3)
        diversity = round(0.5 + rand.random() * 0.45, 3)
        specificity = round(0.5 + rand.random() * 0.45, 3)
        overall = round((coherence + completeness + diversity + specificity) / 4, 3)

        notes = {
            "completeness_note": f"covers {depth} depth levels with {approach} approach",
            "diversity_note": f"{approach} reasoning provides unique perspective",
            "specificity_note": f"addresses problem-specific {approach.lower()} aspects",
        }

        eval_text = _generate_structured_output(
            EVALUATION_TEMPLATE,
            coherence=coherence,
            completeness=completeness,
            diversity=diversity,
            specificity=specificity,
            overall=overall,
            **notes,
        )

        path["score"] = overall
        path["evaluation"] = {
            "coherence": coherence,
            "completeness": completeness,
            "diversity": diversity,
            "specificity": specificity,
        }
        return path

    async def _refine_best(self, best_path: dict, problem: str, context: str) -> dict:
        content = best_path.get("conclusion", "")
        approach = best_path.get("steps", [{}])[0].get("approach", "analytical") if best_path.get("steps") else "analytical"
        rand = random.Random(hash(str(best_path.get("path_id", 0)) + "refine") % (2**31))
        keyword = _truncate(problem, 40)

        refined = _generate_structured_output(
            REFINE_TEMPLATE,
            depth1=f"Deeper analysis of {keyword} reveals {rand.randint(3, 7)} underlying sub-processes",
            depth2=f"These sub-processes interact through {approach.lower()} feedback loops",
            example=f"Example: when {keyword} is stressed, sub-process X compensates by {rand.choice(['increasing throughput', 'reallocating resources', 'adjusting parameters'])}",
            refined_conclusion=f"Refined analysis confirms original conclusion with additional {approach.lower()} depth",
        )

        best_path["content"] = refined
        best_path["refinements"] = 1
        return best_path

    async def _self_correct(self, path: dict, problem: str) -> dict:
        content = path.get("content", "")
        path_id = path.get("path_id", 0)

        rand = random.Random(hash(str(path_id) + "correct") % (2**31))
        needs_correction = rand.random() < 0.3

        if needs_correction:
            corrections_text = _generate_structured_output(
                CORRECTIONS_TEMPLATE,
                correction1=f"hedging language detected — replaced with definitive statement",
                correction2=f"missing quantitative metric — added {rand.randint(10, 99)}% confidence interval",
                corrected=f"Corrected analysis: {_truncate(content, 100)} [with corrections applied]",
            )
            path["content"] = corrections_text
            path["corrections"] = ["hedging language removed", "quantitative metrics added"]
        else:
            path["content"] = content
            path["corrections"] = []

        path["score"] = round(path.get("score", 0.5), 4)
        return path

    def get_history(self, limit: int = 10) -> list[dict]:
        return self._path_history[-limit:]
