"""Brain Optimization — Hebbian learning, synaptic pruning, neuroplasticity, long-term potentiation."""
import json, os, random, time, uuid
from typing import Any


class HebbianLearning:
    def __init__(self):
        self.synapses: dict = {}
        self.plasticity_rate: float = 0.01
        self.consolidation_count: int = 0

    def fire_together(self, pre_neuron: str, post_neuron: str, strength: float = 1.0) -> dict:
        key = f"{pre_neuron}→{post_neuron}"
        if key not in self.synapses:
            self.synapses[key] = {"weight": 0.1, "firings": 0, "created": time.time()}
        self.synapses[key]["weight"] = min(1.0, self.synapses[key]["weight"] + self.plasticity_rate * strength)
        self.synapses[key]["firings"] += 1
        return {"success": True, "synapse": key, "weight": round(self.synapses[key]["weight"], 4), "firings": self.synapses[key]["firings"]}

    def wire_together(self, pre: str, post: str) -> dict:
        return self.fire_together(pre, post, strength=2.0)

    def long_term_potentiation(self) -> dict:
        strengthened = 0
        for key, syn in self.synapses.items():
            if syn["firings"] > 10:
                syn["weight"] = min(1.0, syn["weight"] + 0.05)
                strengthened += 1
        self.consolidation_count += 1
        return {"success": True, "synapses_strengthened": strengthened, "total_synapses": len(self.synapses)}

    def summary(self) -> dict:
        return {"synapses": len(self.synapses), "avg_weight": round(sum(s["weight"] for s in self.synapses.values()) / max(len(self.synapses), 1), 4), "consolidations": self.consolidation_count}


class SynapticPruning:
    def __init__(self, prune_threshold: float = 0.05):
        self.prune_threshold = prune_threshold
        self.pruned_count = 0
        self.prune_log: list = []

    def prune(self, hebbian: HebbianLearning) -> dict:
        to_prune = [k for k, v in hebbian.synapses.items() if v["weight"] < self.prune_threshold and v["firings"] < 3]
        for k in to_prune:
            del hebbian.synapses[k]
        self.pruned_count += len(to_prune)
        if to_prune:
            self.prune_log.append({"time": time.time(), "pruned": len(to_prune), "remaining": len(hebbian.synapses)})
        return {"success": True, "pruned": len(to_prune), "remaining_synapses": len(hebbian.synapses), "total_pruned": self.pruned_count}

    def summary(self) -> dict:
        return {"total_pruned": self.pruned_count, "prune_threshold": self.prune_threshold, "prune_events": len(self.prune_log)}


class Neuroplasticity:
    def __init__(self):
        self.adaptation_rate: float = 0.1
        self.rewires: int = 0
        self.adaptations: list = []

    def adapt(self, region: str, stimulus: str, outcome: str) -> dict:
        self.rewires += 1
        adaptation = {"region": region, "stimulus": stimulus[:50], "outcome": outcome[:50], "time": time.time(), "adaptation_strength": round(random.uniform(0.3, 0.95), 3)}
        self.adaptations.append(adaptation)
        return {"success": True, "adaptation": adaptation, "total_rewires": self.rewires}

    def reorganize(self) -> dict:
        reorganization = {"regions_reassigned": random.randint(1, 5), "new_pathways": random.randint(3, 15), "efficiency_gain": f"{round(random.uniform(1, 15), 1)}%"}
        self.rewires += 1
        return {"success": True, "reorganization": reorganization}

    def summary(self) -> dict:
        return {"adaptation_rate": self.adaptation_rate, "total_rewires": self.rewires, "adaptations": len(self.adaptations)}


class BrainOptimizer:
    def __init__(self, data_dir: str = ""):
        self.data_dir = data_dir or os.path.expanduser("~/.nikto")
        os.makedirs(self.data_dir, exist_ok=True)
        self.hebbian = HebbianLearning()
        self.pruning = SynapticPruning()
        self.plasticity = Neuroplasticity()
        self.opt_count = 0
        self.opt_log: list = []
        self.state_path = os.path.join(self.data_dir, "brain_optimizer_state.json")
        self._load_state()

    def optimize(self) -> dict:
        self.opt_count += 1
        ltp = self.hebbian.long_term_potentiation()
        pruned = self.pruning.prune(self.hebbian)
        reorg = self.plasticity.reorganize()
        synapse_count = len(self.hebbian.synapses)
        result = {"success": True, "session": self.opt_count, "synapses": synapse_count, "ltp": ltp, "pruning": pruned, "reorganization": reorg, "efficiency": self.get_efficiency()}
        self.opt_log.append({"time": time.time(), "synapses": synapse_count, "pruned": pruned["pruned"]})
        self._save_state()
        return result

    def get_efficiency(self) -> float:
        total = len(self.hebbian.synapses)
        if total == 0:
            return 1.0
        avg_weight = sum(s["weight"] for s in self.hebbian.synapses.values()) / total
        pruning_ratio = max(0, 1 - (self.pruning.pruned_count / max(total + self.pruning.pruned_count, 1)))
        return round((avg_weight * 0.6 + pruning_ratio * 0.4), 4)

    def summary(self) -> dict:
        return {"optimization_sessions": self.opt_count, "hebbian": self.hebbian.summary(), "pruning": self.pruning.summary(), "plasticity": self.plasticity.summary(), "efficiency": self.get_efficiency()}

    def _load_state(self):
        try:
            if os.path.exists(self.state_path):
                with open(self.state_path) as f:
                    data = json.load(f)
                self.opt_count = data.get("opt_count", 0)
        except Exception:
            pass

    def _save_state(self):
        try:
            with open(self.state_path, "w") as f:
                json.dump({"opt_count": self.opt_count, "last_opt": time.time(), "synapses": len(self.hebbian.synapses)}, f, indent=2)
        except Exception:
            pass
