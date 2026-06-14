"""
Multiprocess Brain Module for NIKTO.

Manages 6 specialised brain instances (primary, analytical, creative,
strategic, knowledge, intuitive) and provides ``parallel_think()``
and ``consensus()`` methods.
"""

import concurrent.futures
import time
from typing import Any, Optional


class MultiprocessBrain:
    """Orchestrates 6 specialised brain instances.

    Each brain runs a ``process()`` call through
    ``concurrent.futures.ThreadPoolExecutor``.
    """

    _BRAIN_SPECS: dict[str, dict[str, Any]] = {
        "primary": {
            "description": "General-purpose reasoning and decision-making",
            "default_prompt": "Analyze the input comprehensively and provide a balanced response.",
        },
        "analytical": {
            "description": "Logical analysis, pattern detection, deep reasoning",
            "default_prompt": "Break down the input logically. Identify patterns, causes, and effects.",
        },
        "creative": {
            "description": "Novel idea generation, divergent thinking, innovation",
            "default_prompt": "Generate creative ideas and novel perspectives on the input.",
        },
        "strategic": {
            "description": "Long-term planning, goal optimisation, resource allocation",
            "default_prompt": "Evaluate the input from a strategic perspective. Consider long-term implications.",
        },
        "knowledge": {
            "description": "Factual recall, knowledge base query, information synthesis",
            "default_prompt": "Retrieve and synthesise relevant knowledge about the input.",
        },
        "intuitive": {
            "description": "Rapid pattern matching, gut-feel reasoning, holistic assessment",
            "default_prompt": "Provide an intuitive assessment of the input based on pattern recognition.",
        },
    }

    def __init__(self) -> None:
        self.brains: dict[str, dict[str, Any]] = {}
        self._history: list[dict[str, Any]] = []
        for name, spec in self._BRAIN_SPECS.items():
            self.brains[name] = {
                "name": name,
                "config": dict(spec),
                "cycles": 0,
                "last_output": "",
            }

    def parallel_think(self, input_text: str) -> dict[str, Any]:
        """Run all 6 brains concurrently and return results."""
        results: dict[str, Any] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            future_map = {
                executor.submit(self._brain_process, name, input_text): name
                for name in self.brains
            }
            for future in concurrent.futures.as_completed(future_map):
                name = future_map[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    results[name] = {"error": str(e)}

        summary = self._consensus(results)
        record = {
            "input": input_text,
            "timestamp": time.time(),
            "results": results,
            "consensus": summary,
        }
        self._history.append(record)
        return record

    def _brain_process(self, name: str, input_text: str) -> dict[str, Any]:
        """Simulate a brain processing the input."""
        spec = self.brains[name]
        spec["cycles"] += 1
        output = f"[{name.title()} Brain] Processing: {input_text[:80]} | Style: {spec['config']['description']}"
        spec["last_output"] = output
        return {
            "brain": name,
            "output": output,
            "cycles": spec["cycles"],
            "specialization": spec["config"]["description"],
        }

    def consensus(self, results: list[dict[str, Any]]) -> str:
        """Synthesise multiple brain outputs into a single consensus string."""
        if not results:
            return "No results to synthesise."
        opinions = [r.get("output", "") for r in results if isinstance(r, dict)]
        return " | ".join(opinions) if opinions else "No consensus reached."

    def _consensus(self, results: dict[str, Any]) -> dict[str, Any]:
        """Build a consensus summary dict."""
        agreed = len(results)
        return {
            "agreed_count": agreed,
            "total_brains": len(self.brains),
            "agreement_ratio": agreed / max(len(self.brains), 1),
        }

    def get_brain(self, name: str) -> Optional[dict[str, Any]]:
        """Return the brain dict for *name*, or ``None``."""
        return self.brains.get(name)

    def get_status(self) -> dict[str, Any]:
        """Return overall status."""
        return {
            "total_brains": len(self.brains),
            "brains": {n: {"cycles": b["cycles"]} for n, b in self.brains.items()},
            "history_length": len(self._history),
        }

    def get_all_states(self) -> dict[str, Any]:
        """Return state of every brain."""
        return {n: {"cycles": b["cycles"], "last_output": b["last_output"][:100]} for n, b in self.brains.items()}
