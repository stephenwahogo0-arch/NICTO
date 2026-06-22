import json
import os
import time
from typing import Any, Dict, List, Optional


class TrainingCostEstimator:
    def __init__(self, performance_memory=None):
        self.memory = performance_memory
        self.logged_runs: List[Dict] = []
        self.coefficients = {
            "gpu_minutes_per_sample": 0.001,
            "cpu_hours_per_sample": 0.01,
            "memory_gb_per_sample": 0.0005,
            "cost_per_gpu_minute": 0.10,
            "cost_per_cpu_hour": 0.05,
        }
        self._load_logs()

    def _load_logs(self) -> None:
        if self.memory:
            self.logged_runs = self.memory.get_performance_history("training_cost")
        else:
            home = os.path.expanduser("~")
            path = os.path.join(home, ".nikto", "training_costs.json")
            if os.path.exists(path):
                try:
                    with open(path, "r") as f:
                        self.logged_runs = json.load(f)
                except Exception:
                    self.logged_runs = []

    def _save_logs(self) -> None:
        if self.memory:
            for run in self.logged_runs:
                self.memory.store_performance({"metric": "training_cost", **run})
        else:
            home = os.path.expanduser("~")
            os.makedirs(os.path.join(home, ".nikto"), exist_ok=True)
            path = os.path.join(home, ".nikto", "training_costs.json")
            with open(path, "w") as f:
                json.dump(self.logged_runs, f, indent=2)

    def estimate(self, dataset_size: int, model_type: str, epochs: int = 10,
                 batch_size: int = 32, device: str = "cpu") -> Dict:
        c = self.coefficients
        if len(self.logged_runs) >= 5:
            recent = self.logged_runs[-5:]
            gpu_rates = [r.get("gpu_minutes", 0) / max(r.get("samples", 1), 1) for r in recent if r.get("gpu_minutes", 0) > 0]
            cpu_rates = [r.get("cpu_hours", 0) / max(r.get("samples", 1), 1) for r in recent if r.get("cpu_hours", 0) > 0]
            mem_rates = [r.get("memory_gb", 1) / max(r.get("samples", 1), 1) for r in recent if r.get("memory_gb", 1) > 0]
            if gpu_rates:
                c["gpu_minutes_per_sample"] = sum(gpu_rates) / len(gpu_rates)
            if cpu_rates:
                c["cpu_hours_per_sample"] = sum(cpu_rates) / len(cpu_rates)
            if mem_rates:
                c["memory_gb_per_sample"] = sum(mem_rates) / len(mem_rates)

        samples = dataset_size * epochs
        if device == "cuda":
            gpu_minutes = samples * c["gpu_minutes_per_sample"] * (32.0 / max(batch_size, 1))
            cpu_hours = samples * c["cpu_hours_per_sample"] * 0.1 * (32.0 / max(batch_size, 1))
        else:
            gpu_minutes = 0
            cpu_hours = samples * c["cpu_hours_per_sample"] * (32.0 / max(batch_size, 1))
        memory_gb = dataset_size * c["memory_gb_per_sample"] + 0.5
        estimated_cost_usd = gpu_minutes * c["cost_per_gpu_minute"] + cpu_hours * c["cost_per_cpu_hour"]

        return {
            "dataset_size": dataset_size,
            "model_type": model_type,
            "epochs": epochs,
            "batch_size": batch_size,
            "device": device,
            "estimated_gpu_minutes": round(gpu_minutes, 2),
            "estimated_cpu_hours": round(cpu_hours, 2),
            "estimated_memory_gb": round(memory_gb, 2),
            "estimated_cost_usd": round(estimated_cost_usd, 4),
            "total_samples": samples,
        }

    def record_actual(self, training_id: str, actual: Dict) -> None:
        record = {
            "training_id": training_id,
            "samples": actual.get("samples", 0),
            "gpu_minutes": actual.get("gpu_minutes", 0),
            "cpu_hours": actual.get("cpu_hours", 0),
            "memory_gb": actual.get("memory_gb", 0),
            "actual_cost_usd": actual.get("actual_cost_usd", 0),
            "epochs": actual.get("epochs", 0),
            "batch_size": actual.get("batch_size", 32),
            "timestamp": time.time(),
        }
        self.logged_runs.append(record)
        if len(self.logged_runs) > 100:
            self.logged_runs = self.logged_runs[-100:]
        self._save_logs()

    def update_model(self, actual_runs: List[Dict]) -> None:
        if not actual_runs:
            return
        for run in actual_runs:
            if run.get("samples", 0) > 0:
                self.logged_runs.append(run)
        if len(self.logged_runs) > 100:
            self.logged_runs = self.logged_runs[-100:]
        if len(self.logged_runs) >= 5:
            recent = self.logged_runs[-5:]
            gpu_rates = [r.get("gpu_minutes", 0) / max(r.get("samples", 1), 1) for r in recent if r.get("gpu_minutes", 0) > 0]
            cpu_rates = [r.get("cpu_hours", 0) / max(r.get("samples", 1), 1) for r in recent if r.get("cpu_hours", 0) > 0]
            if gpu_rates:
                self.coefficients["gpu_minutes_per_sample"] = sum(gpu_rates) / len(gpu_rates)
            if cpu_rates:
                self.coefficients["cpu_hours_per_sample"] = sum(cpu_rates) / len(cpu_rates)
        self._save_logs()
