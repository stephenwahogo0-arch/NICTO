"""Continuous Improvement Engine — auto-detects weaknesses, runs diagnostics, generates fixes, retrains."""
import json, os, random, time, uuid, traceback
from typing import Any


class ImprovementCycle:
    def __init__(self, name: str, check_fn, improve_fn):
        self.name = name
        self.check_fn = check_fn
        self.improve_fn = improve_fn
        self.last_check = 0.0
        self.issues_found = 0
        self.improvements_made = 0
        self.history: list = []

    def run(self) -> dict:
        try:
            check_result = self.check_fn()
            has_issue = not check_result.get("success", True)
            if has_issue:
                self.issues_found += 1
                improve_result = self.improve_fn(check_result)
                if improve_result.get("success"):
                    self.improvements_made += 1
            self.last_check = time.time()
            entry = {"time": self.last_check, "name": self.name, "has_issue": has_issue, "improved": has_issue}
            self.history.append(entry)
            return {"success": True, "name": self.name, "has_issue": has_issue, "improved": has_issue and self.improvements_made > 0}
        except Exception as e:
            return {"success": False, "name": self.name, "error": str(e)}


class ContinuousImprovement:
    def __init__(self, data_dir: str = ""):
        self.data_dir = data_dir or os.path.expanduser("~/.nikto")
        self.cycles: dict[str, ImprovementCycle] = {}
        self.total_improvements = 0
        self.state_path = os.path.join(self.data_dir, "improvement_state.json")
        self._load_state()

    def register_cycle(self, name: str, check_fn, improve_fn):
        self.cycles[name] = ImprovementCycle(name, check_fn, improve_fn)

    def run_all(self) -> dict:
        results = {}
        for name, cycle in self.cycles.items():
            results[name] = cycle.run()
            if results[name].get("improved"):
                self.total_improvements += 1
        self._save_state()
        return {"success": True, "cycles_run": len(results), "improvements": self.total_improvements, "results": results}

    def weak_spot_scan(self, agent) -> dict:
        weaknesses = []
        if hasattr(agent, "diagnostics"):
            health = agent.diagnostics.system_health()
            if health.get("status") == "degraded":
                weaknesses.append("diagnostics_degraded")
        if hasattr(agent, "resilience"):
            report = agent.resilience.health_report()
            if report.get("watchdogs", {}).get("healthy", 1) < report.get("watchdogs", {}).get("total", 1):
                weaknesses.append("watchdog_failures")
        if hasattr(agent, "brain_optimizer"):
            eff = agent.brain_optimizer.get_efficiency()
            if eff < 0.3:
                weaknesses.append("brain_efficiency_low")
        return {"success": True, "weaknesses": weaknesses, "count": len(weaknesses)}

    def summary(self) -> dict:
        return {"cycles": len(self.cycles), "total_improvements": self.total_improvements, "cycle_names": list(self.cycles.keys())}

    def _load_state(self):
        try:
            if os.path.exists(self.state_path):
                with open(self.state_path) as f:
                    data = json.load(f)
                self.total_improvements = data.get("total_improvements", 0)
        except Exception:
            pass

    def _save_state(self):
        try:
            with open(self.state_path, "w") as f:
                json.dump({"total_improvements": self.total_improvements, "last_run": time.time()}, f, indent=2)
        except Exception:
            pass
