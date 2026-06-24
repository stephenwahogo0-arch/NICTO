"""NICTO X — Multi-path Tree-of-Thought with Anthropic API for real reasoning, self-correction, and recursive refinement."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Optional

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

logger = logging.getLogger("nicto_x.reasoning.tot")

SYSTEM_PROMPT = """You are a multi-path reasoning engine. For each reasoning path, produce a step-by-step analysis using a specific reasoning approach. Be thorough, specific, and rigorous. Output your reasoning steps and a final conclusion."""


class TreeOfThought:
    """Multi-path reasoning with real Anthropic API calls, self-evaluation, branching, and recursive refinement."""

    def __init__(self, max_paths: int = 5, max_depth: int = 5, branching_factor: int = 3):
        self.max_paths = max_paths
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        self._path_history: list[dict] = []
        self._client: Optional[AsyncAnthropic] = None

    def _get_client(self) -> AsyncAnthropic:
        if self._client is None:
            api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("NIKTO_ANTHROPIC_KEY")
            if AsyncAnthropic is None:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set. Set environment variable or configure NIKTO_ANTHROPIC_KEY")
            self._client = AsyncAnthropic(api_key=api_key)
        return self._client

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

    async def _call_anthropic(self, prompt: str, system: str = SYSTEM_PROMPT, max_tokens: int = 1024) -> str:
        client = self._get_client()
        try:
            msg = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text.strip()
        except Exception as e:
            logger.warning(f"Anthropic API call failed: {e}")
            return f"[Reasoning step failed: {e}]"

    async def _generate_cot_paths(self, problem: str, context: str) -> list[dict]:
        approaches = [
            "analytical", "deductive", "inductive", "abductive", "analogical",
            "critical", "creative", "systematic", "empirical", "first_principles",
        ]
        paths = []
        tasks = []
        for i in range(self.max_paths):
            depth = min(i + 2, self.max_depth)
            approach = approaches[i % len(approaches)]
            prompt = (
                f"Using {approach} reasoning, analyze this problem step by step.\n\n"
                f"Problem: {problem}\n"
                f"Context: {context}\n\n"
                f"Provide exactly {depth} reasoning steps and a final conclusion. "
                f"Format as:\nStep 1: ...\nStep 2: ...\n...\nConclusion: ..."
            )
            tasks.append(self._call_anthropic(prompt))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            approach = approaches[i % len(approaches)]
            depth = min(i + 2, self.max_depth)
            if isinstance(result, Exception):
                steps = [{"step": 1, "approach": approach, "content": f"Reasoning failed: {result}"}]
                conclusion = f"Path {i + 1} conclusion: Analysis failed."
            else:
                lines = result.split("\n")
                steps = []
                conclusion = ""
                for line in lines:
                    if line.lower().startswith("step"):
                        step_num = len(steps) + 1
                        steps.append({"step": step_num, "approach": approach, "content": line.strip()})
                    elif line.lower().startswith("conclusion"):
                        conclusion = line.strip()
                if not steps:
                    steps = [{"step": 1, "approach": approach, "content": result[:200]}]
                if not conclusion:
                    conclusion = f"Path {i + 1} conclusion: {result[-200:] if len(result) > 200 else result}"

            paths.append({
                "path_id": i,
                "steps": steps,
                "conclusion": conclusion,
                "depth": depth,
            })
        return paths

    async def _evaluate_path(self, path: dict, problem: str) -> dict:
        content = path.get("conclusion", "")
        steps_text = "\n".join(s.get("content", "") for s in path.get("steps", []))
        prompt = (
            f"Evaluate this reasoning path for the problem: {problem}\n\n"
            f"Steps: {steps_text}\n"
            f"Conclusion: {content}\n\n"
            f"Rate from 0.0 to 1.0 on: coherence, completeness, diversity of reasoning, specificity to the problem. "
            f"Output as JSON: {{\"coherence\": 0.0, \"completeness\": 0.0, \"diversity\": 0.0, \"specificity\": 0.0, \"overall\": 0.0}}"
        )
        try:
            result = await self._call_anthropic(prompt, max_tokens=256)
            import json as json_mod
            import re
            json_match = re.search(r'\{[^}]+\}', result)
            if json_match:
                ev = json_mod.loads(json_match.group())
                overall = ev.get("overall", 0)
                path["score"] = round(overall, 4)
                path["evaluation"] = {k: round(v, 3) for k, v in ev.items() if k != "overall"}
            else:
                raise ValueError("No JSON found in evaluation")
        except Exception as e:
            path["score"] = 0.5
            path["evaluation"] = {"coherence": 0.5, "completeness": 0.5, "diversity": 0.5, "specificity": 0.5, "error": str(e)}
        return path

    async def _refine_best(self, best_path: dict, problem: str, context: str) -> dict:
        content = best_path.get("conclusion", "")
        steps_text = "\n".join(s.get("content", "") for s in best_path.get("steps", []))
        prompt = (
            f"Refine and expand this reasoning for the problem: {problem}\n"
            f"Context: {context}\n\n"
            f"Current analysis:\n{steps_text}\n{content}\n\n"
            f"Provide a more detailed, specific, and rigorous analysis. Add depth, examples, and concrete conclusions."
        )
        try:
            refined = await self._call_anthropic(prompt, max_tokens=1536)
            best_path["content"] = refined
            best_path["refinements"] = 1
        except Exception as e:
            best_path["content"] = content
            best_path["refinements"] = 0
        return best_path

    async def _self_correct(self, path: dict, problem: str) -> dict:
        content = path.get("content", "")
        prompt = (
            f"Review this analysis for errors, contradictions, or hedging language: {content}\n\n"
            f"Problem context: {problem}\n\n"
            f"List any corrections needed as bullet points. If none, say 'No corrections needed.'"
        )
        try:
            review = await self._call_anthropic(prompt, max_tokens=512)
            corrections = []
            for line in review.split("\n"):
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    corrections.append(line.strip().lstrip("-* "))

            if "No corrections needed" not in review:
                correction_prompt = (
                    f"Original analysis: {content}\n\n"
                    f"Corrections needed:\n{review}\n\n"
                    f"Produce the corrected analysis."
                )
                corrected = await self._call_anthropic(correction_prompt, max_tokens=1536)
                path["content"] = corrected
            else:
                path["content"] = content

            path["corrections"] = corrections if corrections else []
        except Exception as e:
            path["content"] = content
            path["corrections"] = []

        path["score"] = round(path.get("score", 0.5), 4)
        return path

    def get_history(self, limit: int = 10) -> list[dict]:
        return self._path_history[-limit:]
