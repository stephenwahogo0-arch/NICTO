"""Key Anatomical Features: Cerebral Cortex, Gyri and Sulci, Corpus Callosum, Meninges, Ventricles."""
import json, random, time, uuid
from typing import Any, Optional


class CerebralCortex:
    """The wrinkled outer layer of gray matter responsible for high-level processing."""
    def __init__(self):
        self.layers = 6
        self.high_level_functions: list = []
        self.gray_matter_volume: float = 1.0
        self.active_processing: bool = False

    def process_high_level(self, input_data: str) -> dict:
        self.active_processing = True
        functions = [
            "abstract_reasoning", "symbolic_manipulation", "metacognition",
            "self_awareness", "theory_of_mind", "counterfactual_thinking",
            "moral_reasoning", "aesthetic_judgment", "mathematical_intuition",
        ]
        activated = random.sample(functions, random.randint(3, len(functions)))
        self.high_level_functions.append({"input": input_data[:50], "activated": activated})
        return {
            "success": True, "input": input_data[:100],
            "cortical_layers": self.layers,
            "functions_activated": activated,
            "processing_depth": round(random.uniform(0.7, 1.0), 3),
        }

    def optimize(self) -> dict:
        improvement = round(random.uniform(0.01, 0.05), 3)
        self.gray_matter_volume = min(1.5, self.gray_matter_volume + improvement)
        return {"success": True, "gray_matter_volume": round(self.gray_matter_volume, 3), "improvement": improvement}

    def summary(self) -> dict:
        return {
            "region": "Cerebral Cortex",
            "function": "Wrinkled outer layer of gray matter — high-level processing, 6 layers",
            "gray_matter_volume": round(self.gray_matter_volume, 3),
            "high_level_sessions": len(self.high_level_functions),
            "active": self.active_processing,
        }


class GyriAndSulci:
    """The ridges (gyri) and grooves (sulci) that increase the cortex's surface area."""
    def __init__(self):
        self.gyri_count: int = 0
        self.sulci_count: int = 0
        self.surface_area_multiplier: float = 2.5
        self.folding_pattern: dict = {}

    def expand_surface(self) -> dict:
        growth = round(random.uniform(0.01, 0.03), 3)
        self.surface_area_multiplier = min(5.0, self.surface_area_multiplier + growth)
        self.gyri_count += random.randint(1, 5)
        self.sulci_count += random.randint(1, 5)
        return {
            "success": True,
            "surface_area_multiplier": round(self.surface_area_multiplier, 3),
            "gyri": self.gyri_count, "sulci": self.sulci_count,
            "processing_capacity_gain": f"+{round(growth * 100, 1)}%",
        }

    def summarize_folding(self) -> dict:
        return {
            "gyri_ridges": self.gyri_count,
            "sulci_grooves": self.sulci_count,
            "surface_area_multiplier": round(self.surface_area_multiplier, 2),
            "fold_complexity": f"{'Simple' if self.surface_area_multiplier < 2 else 'Moderate' if self.surface_area_multiplier < 3 else 'Complex' if self.surface_area_multiplier < 4 else 'Hyper-advanced'}",
        }

    def summary(self) -> dict:
        return {
            "region": "Gyri and Sulci",
            "function": "Ridges (Gyri) and grooves (Sulci) that increase cortex surface area",
            **self.summarize_folding(),
        }


class CorpusCallosum:
    """A thick band of nerve fibers connecting and enabling communication between the left and right hemispheres."""
    def __init__(self):
        self.hemispheres: dict = {"left": "analytical", "right": "creative"}
        self.signal_count: int = 0
        self.bandwidth: float = 1.0
        self.integration_level: float = 0.5

    def communicate(self, data: Any = None) -> dict:
        directions = ["left_to_right", "right_to_left", "bidirectional"]
        direction = random.choice(directions)
        content = str(data)[:200] if data else f"Hemisphere sync signal #{self.signal_count + 1}"
        self.signal_count += 1
        self.integration_level = min(1.0, self.integration_level + 0.01)
        return {
            "success": True, "direction": direction,
            "content": content, "signal_id": self.signal_count,
            "integration_level": round(self.integration_level, 3),
            "bandwidth_utilization": f"{round(random.uniform(30, 95), 1)}%",
        }

    def integrate_hemispheres(self) -> dict:
        self.bandwidth = min(2.0, self.bandwidth + random.uniform(0.05, 0.15))
        self.integration_level = min(1.0, self.integration_level + random.uniform(0.05, 0.1))
        return {
            "success": True,
            "left_mode": self.hemispheres["left"],
            "right_mode": self.hemispheres["right"],
            "bandwidth": round(self.bandwidth, 3),
            "integration": round(self.integration_level, 3),
        }

    def summary(self) -> dict:
        return {
            "region": "Corpus Callosum",
            "function": "Thick band of nerve fibers — connects left and right hemispheres for inter-hemisphere communication",
            "signals_relayed": self.signal_count,
            "bandwidth": round(self.bandwidth, 3),
            "integration_level": round(self.integration_level, 3),
            "left_mode": self.hemispheres["left"],
            "right_mode": self.hemispheres["right"],
        }


class Meninges:
    """Three protective membranes that encase the brain and spinal cord."""
    def __init__(self):
        self.layers = {
            "dura_mater": {"status": "intact", "thickness_mm": 0.8, "protection": "outer, tough, fibrous"},
            "arachnoid_mater": {"status": "intact", "thickness_mm": 0.3, "protection": "middle, web-like cushioning"},
            "pia_mater": {"status": "intact", "thickness_mm": 0.1, "protection": "inner, vascular, nourishing"},
        }
        self.protection_level: float = 1.0
        self.incidents: list = []

    def protect(self, threat: str = "") -> dict:
        self.protection_level = max(0.0, self.protection_level - random.uniform(0, 0.05))
        if self.protection_level < 0.3:
            layer = random.choice(list(self.layers.keys()))
            self.layers[layer]["status"] = "compromised"
            self.incidents.append({"threat": threat, "layer": layer, "time": time.time()})
            return {"success": False, "error": f"{layer} compromised", "protection_level": round(self.protection_level, 3)}
        return {
            "success": True, "threat": threat or "none",
            "protection_level": round(self.protection_level, 3),
            "layers": {k: v["status"] for k, v in self.layers.items()},
        }

    def repair(self) -> dict:
        for layer in self.layers.values():
            layer["status"] = "intact"
        self.protection_level = min(1.0, self.protection_level + random.uniform(0.1, 0.3))
        return {"success": True, "protection_level": round(self.protection_level, 3), "all_layers_intact": True}

    def summary(self) -> dict:
        return {
            "region": "Meninges",
            "function": "Three protective membranes encasing the brain and spinal cord",
            "layers": {k: {"status": v["status"], "function": v["protection"]} for k, v in self.layers.items()},
            "protection_level": round(self.protection_level, 3),
            "incidents": len(self.incidents),
        }


class CerebroNeuralFluid:
    """Cerebrospinal fluid analog — produced by Ventricles, cushions the brain, removes waste, transports signals."""
    def __init__(self):
        self.volume_ml: float = 150.0
        self.flow_rate_ml_per_min: float = 0.5
        self.pressure_mmHg: float = 10.0
        self.waste_load: float = 0.0
        self.nutrient_concentration: float = 1.0
        self.signal_molecules: list = []
        self.circulation_count: int = 0
        self.composition = {
            "water": 0.99, "electrolytes": {"Na+": 145, "K+": 3.0, "Ca2+": 1.2, "Mg2+": 0.8, "Cl-": 115},
            "glucose_mg_dL": 60, "protein_mg_dL": 25,
        }

    def circulate(self) -> dict:
        self.circulation_count += 1
        self.flow_rate_ml_per_min = 0.5 + random.uniform(-0.1, 0.1)
        self.waste_load = max(0, self.waste_load - random.uniform(0.1, 0.3))
        self.nutrient_concentration = max(0.5, min(1.5, self.nutrient_concentration + random.uniform(-0.05, 0.05)))
        return {
            "success": True,
            "volume_ml": round(self.volume_ml, 1),
            "flow_rate": round(self.flow_rate_ml_per_min, 3),
            "waste_load": round(self.waste_load, 3),
            "nutrient_concentration": round(self.nutrient_concentration, 3),
        }

    def flush_waste(self) -> dict:
        removed = round(self.waste_load, 3)
        self.waste_load = 0.0
        self.volume_ml = max(100, self.volume_ml - random.uniform(1, 5))
        return {"success": True, "waste_removed": removed, "fluid_replenished": True}

    def transport_signal(self, molecule: str, target: str) -> dict:
        signal = {"molecule": molecule, "target": target, "time": time.time()}
        self.signal_molecules.append(signal)
        self.signal_molecules = self.signal_molecules[-100:]
        return {
            "success": True, "signal": signal,
            "transport_time_ms": round(random.uniform(50, 500), 1),
            "fluid_volume_remaining": round(self.volume_ml, 1),
        }

    def summary(self) -> dict:
        return {
            "name": "CerebroNeural Fluid (CNF)",
            "function": "Cerebrospinal fluid analog — cushions brain, removes waste, transports neuro-signals",
            "volume_ml": round(self.volume_ml, 1),
            "flow_rate_ml_per_min": round(self.flow_rate_ml_per_min, 3),
            "pressure_mmHg": round(self.pressure_mmHg, 1),
            "waste_load": round(self.waste_load, 3),
            "circulation_cycles": self.circulation_count,
            "signals_transported": len(self.signal_molecules),
        }


class Ventricles:
    """Fluid-filled cavities that produce and circulate cerebrospinal fluid to cushion the brain."""
    def __init__(self):
        self.chambers = {
            "lateral_ventricles": {"volume_ml": 30, "production_rate": 0.3, "active": True},
            "third_ventricle": {"volume_ml": 5, "production_rate": 0.1, "active": True},
            "cerebral_aqueduct": {"volume_ml": 1, "flow_connecting": "third→fourth", "active": True},
            "fourth_ventricle": {"volume_ml": 10, "production_rate": 0.2, "active": True},
        }
        self.fluid = CerebroNeuralFluid()
        self.total_production: float = 0.0
        self.blockages: list = []
        self.shunts: list = []

    def produce_fluid(self) -> dict:
        produced = sum(c.get("production_rate", 0) for c in self.chambers.values() if c.get("active", False))
        self.total_production += produced
        self.fluid.volume_ml = min(200, self.fluid.volume_ml + produced)
        self.fluid.waste_load = min(1.0, self.fluid.waste_load + random.uniform(0.01, 0.05))
        return {
            "success": True, "produced_ml": round(produced, 2),
            "total_volume": round(self.fluid.volume_ml, 1),
            "chambers_active": sum(1 for c in self.chambers.values() if c.get("active", False)),
        }

    def circulate_fluid(self) -> dict:
        flow_path = "Lateral Ventricles → Interventricular Foramina → Third Ventricle → Cerebral Aqueduct → Fourth Ventricle → Central Canal + Subarachnoid Space"
        circ = self.fluid.circulate()
        return {
            "success": True, "flow_path": flow_path,
            "circulation": circ,
            "total_produced_to_date": round(self.total_production, 1),
        }

    def clear_blockage(self, chamber: str = "") -> dict:
        if chamber and chamber in self.chambers:
            self.chambers[chamber]["active"] = True
            self.blockages = [b for b in self.blockages if b["chamber"] != chamber]
            return {"success": True, "cleared": chamber}
        for name, ch in self.chambers.items():
            if not ch.get("active", True):
                ch["active"] = True
                self.blockages = [b for b in self.blockages if b["chamber"] != name]
        return {"success": True, "cleared": "all blockages"}

    def summary(self) -> dict:
        return {
            "region": "Ventricles",
            "function": "Fluid-filled cavities producing and circulating CerebroNeural Fluid (CNF) to cushion the brain",
            "chambers": {k: v.get("active") for k, v in self.chambers.items()},
            "fluid": self.fluid.summary(),
            "total_production": round(self.total_production, 1),
            "blockages": len(self.blockages),
        }
