"""Self-Diagnostics & Health Monitor — continuous system verification, error tracking, performance metrics."""
import json, os, random, time, uuid, traceback
from typing import Any


class DiagnosticCheck:
    def __init__(self, name: str, check_fn):
        self.name = name
        self.check_fn = check_fn
        self.last_run = 0.0
        self.last_status = "unknown"
        self.last_detail = ""
        self.run_count = 0
        self.fail_count = 0

    def run(self) -> dict:
        self.run_count += 1
        try:
            result = self.check_fn()
            passed = result.get("success", True)
            detail = str(result.get("detail", result))[:200]
            self.last_status = "pass" if passed else "fail"
            if not passed:
                self.fail_count += 1
                self.last_status = "fail"
        except Exception as e:
            self.last_status = "error"
            self.fail_count += 1
            detail = f"{type(e).__name__}: {str(e)[:100]}"
        self.last_detail = detail
        self.last_run = time.time()
        return {"name": self.name, "status": self.last_status, "detail": detail, "run_count": self.run_count, "fail_count": self.fail_count}


class DiagnosticsEngine:
    def __init__(self, data_dir: str = ""):
        self.data_dir = data_dir or os.path.expanduser("~/.nikto")
        os.makedirs(self.data_dir, exist_ok=True)
        self.checks: dict[str, DiagnosticCheck] = {}
        self.error_log: list = []
        self.performance_metrics: dict = {}
        self.start_time = time.time()
        self.state_path = os.path.join(self.data_dir, "diagnostics_state.json")
        self._load_state()

    def register_check(self, name: str, check_fn):
        self.checks[name] = DiagnosticCheck(name, check_fn)

    def run_all(self) -> dict:
        results = {}
        all_pass = True
        for name, check in self.checks.items():
            result = check.run()
            results[name] = result
            if result["status"] != "pass":
                all_pass = False
        return {"success": all_pass, "checks": results, "total": len(results), "passed": sum(1 for r in results.values() if r["status"] == "pass"), "timestamp": time.time()}

    def log_error(self, source: str, error: str, context: str = ""):
        entry = {"source": source, "error": str(error)[:500], "context": str(context)[:500], "time": time.time(), "traceback": traceback.format_exc() if traceback else ""}
        self.error_log.append(entry)
        self.error_log = self.error_log[-1000:]
        self._save_state()

    def track_metric(self, name: str, value: float):
        if name not in self.performance_metrics:
            self.performance_metrics[name] = {"values": [], "min": value, "max": value, "avg": value, "count": 0}
        m = self.performance_metrics[name]
        m["values"].append(value)
        m["values"] = m["values"][-1000:]
        m["min"] = min(m["min"], value)
        m["max"] = max(m["max"], value)
        m["avg"] = round(sum(m["values"][-100:]) / max(len(m["values"][-100:]), 1), 4)
        m["count"] += 1

    def get_metric(self, name: str) -> dict:
        return self.performance_metrics.get(name, {"error": "Metric not found"})

    def system_health(self) -> dict:
        uptime = time.time() - self.start_time
        return {
            "status": "healthy" if len(self.error_log[-100:]) < 50 else "degraded",
            "uptime_seconds": round(uptime, 1),
            "uptime_days": round(uptime / 86400, 4),
            "checks": {n: {"status": c.last_status, "detail": c.last_detail} for n, c in self.checks.items()},
            "recent_errors": len([e for e in self.error_log if e["time"] > time.time() - 3600]),
            "total_errors": len(self.error_log),
            "metrics": {k: {"min": v["min"], "max": v["max"], "avg": v["avg"]} for k, v in self.performance_metrics.items()},
        }

    def _load_state(self):
        try:
            if os.path.exists(self.state_path):
                with open(self.state_path) as f:
                    data = json.load(f)
                self.error_log = data.get("error_log", [])
        except Exception:
            pass

    def _save_state(self):
        try:
            with open(self.state_path, "w") as f:
                json.dump({"error_log": self.error_log[-100:], "last_save": time.time()}, f, indent=2)
        except Exception:
            pass
