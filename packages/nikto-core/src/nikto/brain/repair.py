import os
import sys
import importlib
import subprocess
from datetime import datetime, timezone
from typing import Optional


class HealthReport:
    def __init__(self):
        self.modules = {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def add_result(self, module: str, status: str, detail: str = ""):
        self.modules[module] = {"status": status, "detail": detail}

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class TestReport:
    def __init__(self, total: int, passed: int, failed: int, failures: list):
        self.total = total
        self.passed = passed
        self.failed = failed
        self.failures = failures

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoSelfRepair:
    CRITICAL_MODULES = [
        "kyros.brain.core", "kyros.brain.identity", "kyros.brain.reasoner",
        "kyros.brain.memory", "kyros.brain.knowledge", "kyros.brain.emotion",
        "kyros.brain.conscience", "kyros.brain.language", "kyros.brain.learner",
        "kyros.brain.goals", "kyros.brain.models",
    ]

    async def health_check_all(self) -> HealthReport:
        report = HealthReport()
        for mod_name in self.CRITICAL_MODULES:
            try:
                importlib.import_module(mod_name)
                report.add_result(mod_name, "PASS", "Module imports successfully")
            except ImportError as e:
                report.add_result(mod_name, "FAIL", f"Import error: {e}")
            except Exception as e:
                report.add_result(mod_name, "ERROR", str(e))
        return report

    async def detect_broken_modules(self) -> list:
        broken = []
        for mod_name in self.CRITICAL_MODULES:
            try:
                importlib.import_module(mod_name)
            except Exception:
                broken.append(mod_name)
        return broken

    async def attempt_repair(self, module_path: str) -> bool:
        try:
            importlib.invalidate_caches()
            importlib.import_module(module_path)
            return True
        except ImportError:
            try:
                result = subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."],
                                        capture_output=True, text=True, timeout=60)
                importlib.invalidate_caches()
                importlib.import_module(module_path)
                return True
            except Exception:
                return False
        except Exception:
            return False

    async def run_self_tests(self) -> TestReport:
        failures = []
        passed = 0
        total = len(self.CRITICAL_MODULES)
        for mod_name in self.CRITICAL_MODULES:
            try:
                mod = importlib.import_module(mod_name)
                passed += 1
            except Exception as e:
                failures.append({"module": mod_name, "error": str(e)})
        return TestReport(total, passed, len(failures), failures)

    async def rollback_module(self, module: str) -> bool:
        try:
            importlib.invalidate_caches()
            if module in sys.modules:
                del sys.modules[module]
            return True
        except Exception:
            return False
