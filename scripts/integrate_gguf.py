"""
NICTO NeuralCore GGUF Integration
Loads a trained GGUF model into the NeuralCore inference engine.
Replaces numpy random weights with actual trained weights.
"""
import os, sys, json, logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("nicto.gguf_integration")


class GGUFIntegrator:
    """Bridges trained GGUF models into NICTO's NeuralCore and 4-model pipeline."""

    def __init__(self, models_dir: str = None):
        self.models_dir = Path(models_dir or os.path.expanduser("~/.nicto/trained_models"))
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.loaded_adapters: dict[str, dict] = {}
        self._load_registry()

    def _registry_path(self) -> Path:
        return self.models_dir / "registry.json"

    def _load_registry(self):
        if self._registry_path().exists():
            with open(self._registry_path()) as f:
                self.loaded_adapters = json.load(f)

    def _save_registry(self):
        with open(self._registry_path(), "w") as f:
            json.dump(self.loaded_adapters, f, indent=2)

    def register_model(self, name: str, gguf_path: str, model_type: str,
                       params: str, loss: float = None):
        """Register a trained GGUF model for use by a pipeline."""
        path = Path(gguf_path)
        if not path.exists():
            raise FileNotFoundError(f"GGUF not found: {gguf_path}")

        entry = {
            "name": name,
            "gguf_path": str(path.resolve()),
            "model_type": model_type,
            "params": params,
            "loss": loss,
            "size_mb": round(path.stat().st_size / (1024 * 1024), 1),
            "registered_at": __import__("time").strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.loaded_adapters[name] = entry
        self._save_registry()
        logger.info(f"Registered GGUF model '{name}' ({params}) — {entry['size_mb']}MB")
        return entry

    def get_adapter(self, pipeline: str) -> Optional[dict]:
        """Get the best GGUF adapter for a pipeline (kyros/omega/main/x/universal)."""
        # Exact match first
        if pipeline in self.loaded_adapters:
            return self.loaded_adapters[pipeline]

        # Universal fallback
        if "universal" in self.loaded_adapters:
            return self.loaded_adapters["universal"]

        # Any adapter
        if self.loaded_adapters:
            return list(self.loaded_adapters.values())[0]

        return None

    def load_into_neural_core(self, pipeline: str = "universal"):
        """Load GGUF model into NeuralCore for the given pipeline."""
        adapter = self.get_adapter(pipeline)
        if not adapter:
            logger.warning(f"No trained model for '{pipeline}' — using numpy fallback")
            return None

        gguf_path = adapter["gguf_path"]
        if not os.path.exists(gguf_path):
            logger.warning(f"GGUF file missing: {gguf_path}")
            return None

        try:
            from nicto_x.neural.core import NeuralCore
            from nicto_x.neural.config import NeuralConfig

            # Configure NeuralCore to use GGUF weights
            config = NeuralConfig(
                d_model=4096 if "7B" in adapter["params"] else 3072,
                num_layers=32 if "7B" in adapter["params"] else 24,
                num_heads=32 if "7B" in adapter["params"] else 24,
                num_experts=4,
                top_k=2,
                max_seq_len=32768,
                gguf_path=gguf_path,
            )
            core = NeuralCore(config)
            logger.info(f"NeuralCore loaded with {adapter['name']} ({adapter['params']})")
            return core

        except Exception as e:
            logger.error(f"Failed to load GGUF into NeuralCore: {e}")
            return None

    def get_status(self) -> dict:
        """Get status of all registered models."""
        return {
            "models": self.loaded_adapters,
            "count": len(self.loaded_adapters),
            "pipelines": {
                p: self.get_adapter(p) is not None
                for p in ["kyros", "omega", "main", "x", "universal"]
            },
        }

    def auto_assign_pipelines(self):
        """Auto-assign best adapters to each pipeline based on loss."""
        by_adapter = {}
        for name, entry in self.loaded_adapters.items():
            adapter_type = name.split("_")[-1] if "_" in name else "universal"
            if adapter_type not in by_adapter:
                by_adapter[adapter_type] = []
            by_adapter[adapter_type].append(entry)

        assigned = {}
        for pipeline in ["kyros", "omega", "main", "x", "universal"]:
            candidates = by_adapter.get(pipeline, [])
            if not candidates:
                candidates = by_adapter.get("universal", [])
            if candidates:
                best = min(candidates, key=lambda e: e.get("loss", 999) or 999)
                assigned[pipeline] = best["name"]
            else:
                assigned[pipeline] = None

        return assigned


def integrate_gguf(model_name: str, gguf_path: str, pipeline: str = "universal",
                   model_type: str = "qwen25", params: str = "7B", loss: float = None):
    """Quick one-shot function: register a GGUF and wire into NeuralCore."""
    integrator = GGUFIntegrator()
    integrator.register_model(model_name, gguf_path, model_type, params, loss)
    core = integrator.load_into_neural_core(pipeline)
    return core


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("NICTO GGUF Integration Tool")
    print("Usage:")
    print("  from scripts.integrate_gguf import integrate_gguf")
    print("  core = integrate_gguf('nicto_universal', '/path/to/model.gguf')")
    print()
    print("Current registry:")
    integrator = GGUFIntegrator()
    status = integrator.get_status()
    for name, entry in status["models"].items():
        print(f"  {name}: {entry['params']} ({entry['size_mb']}MB) loss={entry.get('loss', '?')}")
    print(f"  Total: {status['count']} models")
    print(f"  Pipeline assignments: {integrator.auto_assign_pipelines()}")
