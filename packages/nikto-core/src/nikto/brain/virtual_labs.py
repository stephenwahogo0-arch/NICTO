import time
import math
from typing import Optional, Dict, Any, List

_VL_LOADED = False
_VirtualLab = None
try:
    import sys, os
    _root = r"C:\Users\BYU\Desktop\AKNOW##"
    if _root not in sys.path:
        sys.path.insert(0, _root)
    _sdk = os.path.join(_root, "sdk")
    if _sdk not in sys.path:
        sys.path.insert(0, _sdk)
    from aknow_omega import VirtualLab as _VL
    _VirtualLab = _VL
    _VL_LOADED = True
except ImportError:
    pass


LAB_CATEGORIES = {
    "disease_modeling": ["sir", "seir", "sird", "pandemic", "immune_sim", "climate_disease"],
    "drug_discovery": ["drug_sim", "clinical_trial"],
    "genetics": ["mutation_sim"],
    "optimization": ["optimize", "search_solutions"],
}

LAB_DESCRIPTIONS = {
    "sir": "SIR compartment disease model — Susceptible → Infected → Recovered",
    "seir": "SEIR model with incubation period — adds Exposed compartment",
    "sird": "SIRD model with explicit mortality — adds Deceased compartment",
    "pandemic": "Full pandemic simulation with mutation and intervention",
    "drug_sim": "Drug-target binding simulation with dose-response",
    "clinical_trial": "Randomized controlled clinical trial",
    "mutation_sim": "Genetic drift and variant emergence simulation",
    "immune_sim": "Immune response to antigen exposure",
    "climate_disease": "Climate-disease vector model (temperature + humidity)",
    "optimize": "Seed-space search for optimal intervention strategies",
    "search_solutions": "Parallel seed-space exploration with Hydra",
}


class LabResult:
    def __init__(self, lab_name: str, data: dict, seed: int, domain: str, family: str, duration: float):
        self.lab_name = lab_name
        self.data = data
        self.seed = seed
        self.domain = domain
        self.family = family
        self.duration = duration
        self.timestamp = time.time()

    def summary(self) -> str:
        d = self.data
        name = self.lab_name.upper()
        parts = [f"[{name}] seed={self.seed} domain={self.domain}"]
        if "peak_infections" in d:
            parts.append(f"peak={d['peak_infections']} day={d.get('peak_day','?')}")
        if "total_infected" in d:
            parts.append(f"total={d['total_infected']}")
        if "final_D" in d:
            parts.append(f"deaths={d['final_D']}")
        if "case_fatality_rate" in d:
            parts.append(f"CFR={d['case_fatality_rate']*100:.1f}%")
        if "binding_affinity" in d:
            parts.append(f"affinity={d['binding_affinity']}")
        if "IC50" in d:
            parts.append(f"IC50={d['IC50']}")
        if "recovered" in d:
            parts.append(f"recovered={d['recovered']}")
        if "adverse_events" in d:
            parts.append(f"adverse={d['adverse_events']}")
        if "total_cases" in d:
            parts.append(f"cases={d['total_cases']}")
        if "peak_vectors" in d:
            parts.append(f"vectors={d['peak_vectors']}")
        if "score" in d:
            parts.append(f"score={d['score']}")
        return " | ".join(parts)

    def to_dict(self) -> dict:
        return {
            "lab": self.lab_name,
            "seed": self.seed,
            "domain": self.domain,
            "family": self.family,
            "duration_s": round(self.duration, 3),
            "timestamp": self.timestamp,
            "data": self.data,
            "summary": self.summary(),
        }


class NiktoVirtualLabs:
    def __init__(self):
        self._loaded = _VL_LOADED
        self._lab: Optional[Any] = None
        self._results: List[LabResult] = []
        self._init_time = time.time()
        self._stats = {"runs": 0, "errors": 0, "total_duration": 0.0}
        if self._loaded:
            self._lab = _VirtualLab()

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def result_count(self) -> int:
        return len(self._results)

    def list_labs(self) -> List[Dict[str, Any]]:
        return [
            {"name": name, "description": desc, "category": cat}
            for cat, names in LAB_CATEGORIES.items()
            for name in names
            if (desc := LAB_DESCRIPTIONS.get(name, ""))
        ]

    def list_categories(self) -> Dict[str, List[str]]:
        return dict(LAB_CATEGORIES)

    def _run(self, lab_name: str, seed: int, **kwargs) -> Optional[LabResult]:
        if not self._loaded or self._lab is None:
            return None
        fn = getattr(self._lab, lab_name, None)
        if fn is None:
            self._stats["errors"] += 1
            return None

        domain, family = self._resolve_domain(seed)
        t0 = time.perf_counter()
        try:
            data = fn(seed, **kwargs)
        except Exception:
            self._stats["errors"] += 1
            return None
        elapsed = time.perf_counter() - t0

        result = LabResult(lab_name, data, seed, domain, family, elapsed)
        self._results.append(result)
        self._stats["runs"] += 1
        self._stats["total_duration"] += elapsed
        return result

    def _resolve_domain(self, seed: int) -> tuple:
        try:
            from nikto.brain.aknow_bridge import AknowBridge
            a = AknowBridge()
            return a.resolve_domain(seed)
        except Exception:
            return "general", "General"

    def sir(self, seed: int = 42, population: int = 100000, R0: float = 2.5,
            recovery_days: float = 14, days: int = 100) -> Optional[LabResult]:
        return self._run("sir", seed, population=population, R0=R0,
                         recovery_days=recovery_days, days=days)

    def seir(self, seed: int = 42, population: int = 100000, R0: float = 2.5,
             incubation_days: float = 5, recovery_days: float = 14,
             days: int = 120) -> Optional[LabResult]:
        return self._run("seir", seed, population=population, R0=R0,
                         incubation_days=incubation_days, recovery_days=recovery_days, days=days)

    def sird(self, seed: int = 42, population: int = 100000, R0: float = 2.5,
             recovery_days: float = 14, mortality_rate: float = 0.02,
             days: int = 120) -> Optional[LabResult]:
        return self._run("sird", seed, population=population, R0=R0,
                         recovery_days=recovery_days, mortality_rate=mortality_rate, days=days)

    def pandemic(self, seed: int = 42, population: int = 1000000, R0: float = 2.5,
                 mutation_rate: float = 0.001, intervention_day: int = 50,
                 intervention_strength: float = 0.3, days: int = 200) -> Optional[LabResult]:
        return self._run("pandemic", seed, population=population, R0=R0,
                         mutation_rate=mutation_rate, intervention_day=intervention_day,
                         intervention_strength=intervention_strength, days=days)

    def drug_sim(self, seed: int = 42, drug_name: str = "Cmpd-X", dose_mg: float = 100.0,
                 target: str = "3CL-Protease") -> Optional[LabResult]:
        return self._run("drug_sim", seed, drug_name=drug_name, dose_mg=dose_mg, target=target)

    def clinical_trial(self, seed: int = 42, cohort_size: int = 1000,
                       treatment_efficacy: float = 0.7, placebo_effect: float = 0.15,
                       days: int = 30, arms: int = 2) -> Optional[LabResult]:
        return self._run("clinical_trial", seed, cohort_size=cohort_size,
                         treatment_efficacy=treatment_efficacy, placebo_effect=placebo_effect,
                         days=days, arms=arms)

    def mutation_sim(self, seed: int = 42, sequence_length: int = 1000,
                     mutation_rate: float = 0.001, generations: int = 100) -> Optional[LabResult]:
        return self._run("mutation_sim", seed, sequence_length=sequence_length,
                         mutation_rate=mutation_rate, generations=generations)

    def immune_sim(self, seed: int = 42, antigen_strength: float = 0.7,
                   prior_immunity: float = 0.0) -> Optional[LabResult]:
        return self._run("immune_sim", seed, antigen_strength=antigen_strength,
                         prior_immunity=prior_immunity)

    def climate_disease(self, seed: int = 42, temperature_c: float = 25.0,
                        humidity_pct: float = 60.0, vector_population: int = 10000,
                        days: int = 90) -> Optional[LabResult]:
        return self._run("climate_disease", seed, temperature_c=temperature_c,
                         humidity_pct=humidity_pct, vector_population=vector_population, days=days)

    def optimize(self, seed_base: int = 42, problem: str = "pandemic",
                 max_attempts: int = 1000, population: int = 100000,
                 target_reduction: float = 0.5) -> Optional[LabResult]:
        return self._run("optimize", seed_base, problem=problem, max_attempts=max_attempts,
                         population=population, target_reduction=target_reduction)

    def search_solutions(self, seed_base: int = 42, problem: str = "pandemic",
                         attempts: int = 500, parallel_heads: int = 4) -> Optional[LabResult]:
        return self._run("search_solutions", seed_base, problem=problem,
                         attempts=attempts, parallel_heads=parallel_heads)

    def latest_results(self, n: int = 5) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._results[-n:]]

    def latest_summary(self) -> str:
        if not self._results:
            return "No lab results yet."
        lines = [r.summary() for r in self._results[-5:]]
        return "\n".join(lines)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "loaded": self._loaded,
            "runs": self._stats["runs"],
            "errors": self._stats["errors"],
            "total_duration_s": round(self._stats["total_duration"], 3),
            "avg_duration_ms": round(self._stats["total_duration"] / max(self._stats["runs"], 1) * 1000, 2),
            "results_stored": self.result_count,
            "labs_available": len(self.list_labs()),
            "categories": list(LAB_CATEGORIES.keys()),
        }

    def save(self) -> dict:
        return {
            "results": [r.to_dict() for r in self._results],
            "stats": self._stats,
        }

    def load(self, data: dict):
        self._results = []
        for rd in data.get("results", []):
            lab_name = rd.get("lab", "sir")
            result = LabResult(
                lab_name, rd.get("data", {}),
                rd.get("seed", 42),
                rd.get("domain", "general"),
                rd.get("family", "General"),
                rd.get("duration_s", 0),
            )
            result.timestamp = rd.get("timestamp", time.time())
            self._results.append(result)
        self._stats = data.get("stats", {"runs": 0, "errors": 0, "total_duration": 0.0})
