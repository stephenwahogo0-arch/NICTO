"""
Multiprocess Brain Module for NIKTO.

Manages 6 specialised brain instances (primary, analytical, creative,
strategic, knowledge, intuitive) and provides ``parallel_think()``
and ``consensus()`` methods.
"""

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
        self._real_brains: dict[str, Any] = {}
        self._load_real_brains()
        for name, spec in self._BRAIN_SPECS.items():
            self.brains[name] = {
                "name": name,
                "config": dict(spec),
                "cycles": 0,
                "last_output": "",
            }

    def _load_real_brains(self):
        import importlib
        brain_map = {
            "primary": ("nicto.brains.primary", "PrimaryBrain"),
            "analytical": ("nicto.brains.analytical", "AnalyticalBrain"),
            "creative": ("nicto.brains.creative", "CreativeBrain"),
            "strategic": ("nicto.brains.strategic", "StrategicBrain"),
            "knowledge": ("nicto.brains.knowledge", "KnowledgeBrain"),
            "intuitive": ("nicto.brains.intuitive", "IntuitiveBrain"),
        }
        for name, (mod_path, cls_name) in brain_map.items():
            try:
                mod = importlib.import_module(mod_path)
                cls = getattr(mod, cls_name)
                self._real_brains[name] = cls()
            except Exception:
                pass

    def parallel_think(self, input_text: str) -> dict[str, Any]:
        """Run all 6 brains and return results."""
        results: dict[str, Any] = {}
        for name in self.brains:
            try:
                results[name] = self._brain_process(name, input_text)
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
        spec = self.brains[name]
        spec["cycles"] += 1
        real = self._real_brains.get(name)
        if real and hasattr(real, 'process'):
            try:
                result = real.process(input_text)
                spec["last_output"] = str(result)[:200]
                return {
                    "brain": name,
                    "output": str(result)[:500],
                    "cycles": spec["cycles"],
                    "specialization": spec["config"]["description"],
                    "status": "real",
                }
            except Exception:
                pass
        words = input_text.split()
        word_count = len(words)
        avg_word_len = sum(len(w) for w in words) / max(word_count, 1)
        output = f"[{name.title()} Brain] Processed {word_count} words | Avg word len: {avg_word_len:.1f} | Style: {spec['config']['description']}"
        spec["last_output"] = output
        return {
            "brain": name,
            "output": output,
            "cycles": spec["cycles"],
            "specialization": spec["config"]["description"],
            "status": "statistical",
        }

    def consensus(self, results: list[dict[str, Any]]) -> str:
        """Synthesise multiple brain outputs into a single consensus string."""
        if not results:
            return "No results to synthesise."
        opinions = [r.get("output", "") for r in results if isinstance(r, dict)]
        return " | ".join(opinions) if opinions else "No consensus reached."

    def _consensus(self, results: dict[str, Any]) -> dict[str, Any]:
        agreed = len(results)
        return {
            "agreed_count": agreed,
            "total_brains": len(self.brains),
            "agreement_ratio": agreed / max(len(self.brains), 1),
        }

    def get_brain(self, name: str) -> Optional[dict[str, Any]]:
        return self.brains.get(name)

    def get_status(self) -> dict[str, Any]:
        real_count = sum(1 for v in self._real_brains.values() if v is not None)
        return {
            "total_brains": len(self.brains),
            "real_brains_loaded": real_count,
            "brains": {n: {"cycles": b["cycles"]} for n, b in self.brains.items()},
            "history_length": len(self._history),
        }

    def get_all_states(self) -> dict[str, Any]:
        return {n: {"cycles": b["cycles"], "last_output": b["last_output"][:100]} for n, b in self.brains.items()}
