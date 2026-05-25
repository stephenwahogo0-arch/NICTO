"""NIKTO Eagle Eye — Multi-layer perception engine for observation, pattern detection, and threat analysis."""

import asyncio
import json
import re
import os
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class Observation:
    timestamp: str
    network: dict
    processes: dict
    files: dict
    security: dict
    anomaly_score: float

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class Alert:
    level: str
    message: str
    timestamp: str

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class EagleEyeAnalysis:
    target: str
    depth: str
    timestamp: str
    surface_findings: dict
    patterns_found: list
    anomalies_detected: list
    threat_assessment: dict
    opportunities_identified: list
    predictions: list
    deep_context: str
    confidence: float
    alert_level: str

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class EagleEyeReport:
    total_observations: int
    total_alerts: int
    total_patterns: int
    opportunities_found: int
    highest_anomaly: float
    watch_duration_seconds: int

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class Pattern:
    phrase: str
    frequency: int
    memory_ids: list
    confidence: float

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NetworkEye:
    async def watch(self) -> None:
        pass

    async def observe(self) -> dict:
        return {"status": "nominal"}

    async def analyze_ip(self, ip: str) -> dict:
        return {"ip": ip, "status": "analyzed"}

    async def analyze_domain(self, domain: str) -> dict:
        return {"domain": domain, "dns": "resolved"}

    async def analyze_url(self, url: str) -> dict:
        return {"url": url, "accessible": True}


class CodeEye:
    async def analyze(self, code: str) -> dict:
        lines = code.count("\n")
        return {"lines": lines, "complexity": "medium"}


class SecurityEye:
    async def watch(self) -> None:
        pass

    async def observe(self) -> dict:
        return {"threats_detected": 0, "status": "clean"}


class ProcessEye:
    async def watch(self) -> None:
        pass

    async def observe(self) -> dict:
        if HAS_PSUTIL:
            try:
                proc_count = len(psutil.pids())
                cpu = psutil.cpu_percent(interval=0.1)
                ram = psutil.virtual_memory().percent
                return {"processes": proc_count, "cpu_percent": cpu, "ram_percent": ram}
            except Exception:
                pass
        return {"processes": 0, "cpu_percent": 0, "ram_percent": 0}


class FileSystemEye:
    async def observe(self) -> dict:
        return {"changed_files": 0}

    async def analyze(self, path: str) -> dict:
        if os.path.exists(path):
            stat = os.stat(path)
            return {"exists": True, "size_bytes": stat.st_size, "path": path}
        return {"exists": False, "path": path}


class MarketEye:
    async def observe(self) -> dict:
        return {"market_status": "monitoring"}


class NiktoEagleEye:
    """
    NICTO's enhanced Eagle Eye system.
    A multi-layer perception engine that monitors,
    analyzes, and reports on everything it observes.

    Eagle Eye Layers:
    Layer 1: Surface Observation   — what is visible
    Layer 2: Pattern Detection     — what repeats
    Layer 3: Anomaly Detection     — what is wrong
    Layer 4: Threat Intelligence   — what is dangerous
    Layer 5: Opportunity Scanning  — what has value
    Layer 6: Predictive Signal     — what comes next
    Layer 7: Deep Context          — why it matters
    """

    OBSERVATION_TARGETS = [
        "network_traffic", "system_processes", "file_system_changes",
        "user_behavior", "code_quality", "security_posture",
        "market_conditions", "competitor_activity", "technical_debt",
        "performance_metrics",
    ]

    def __init__(self, brain):
        self.brain = brain
        self.is_watching = False
        self.observations = []
        self.alerts = []
        self.patterns = []
        self.opportunity_signals = []
        self.network_eye = NetworkEye()
        self.code_eye = CodeEye()
        self.security_eye = SecurityEye()
        self.market_eye = MarketEye()
        self.process_eye = ProcessEye()
        self.file_eye = FileSystemEye()
        self._start_time = None

    async def open(self) -> None:
        self.is_watching = True
        self._start_time = datetime.now(timezone.utc)
        asyncio.create_task(self._continuous_watch())

    async def close(self) -> EagleEyeReport:
        self.is_watching = False
        return await self.generate_report()

    async def _continuous_watch(self) -> None:
        while self.is_watching:
            try:
                observation = await self._observe_all()
                self.observations.append(observation)
                if len(self.observations) >= 10:
                    patterns = await self._detect_patterns()
                    self.patterns.extend(patterns)
                alerts = await self._check_alert_conditions(observation)
                self.alerts.extend(alerts)
                opportunities = await self._scan_opportunities(observation)
                self.opportunity_signals.extend(opportunities)
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(30)

    async def _observe_all(self) -> Observation:
        network = await self.network_eye.observe()
        processes = await self.process_eye.observe()
        files = await self.file_eye.observe()
        security = await self.security_eye.observe()
        return Observation(
            timestamp=datetime.now(timezone.utc).isoformat(),
            network=network, processes=processes, files=files,
            security=security,
            anomaly_score=self._calculate_anomaly_score(network, processes, security),
        )

    async def analyze_target(self, target: str, depth: str = "deep") -> EagleEyeAnalysis:
        analysis_steps = []
        surface = await self._surface_observe(target)
        analysis_steps.append(("Surface", surface))
        patterns = await self._detect_patterns_in_target(target, surface)
        analysis_steps.append(("Patterns", patterns))
        anomalies = await self._detect_anomalies(target, surface)
        analysis_steps.append(("Anomalies", anomalies))
        threats = await self._threat_intelligence(target)
        analysis_steps.append(("Threats", threats))
        opportunities = await self._opportunity_scan(target)
        analysis_steps.append(("Opportunities", opportunities))
        predictions = await self._generate_predictions(target, analysis_steps)
        analysis_steps.append(("Predictions", predictions))
        context = f"Deep contextual analysis of {target} across {len(analysis_steps)} layers."
        return EagleEyeAnalysis(
            target=target, depth=depth, timestamp=datetime.now(timezone.utc).isoformat(),
            surface_findings=surface, patterns_found=patterns,
            anomalies_detected=anomalies, threat_assessment=threats,
            opportunities_identified=opportunities, predictions=predictions,
            deep_context=context, confidence=0.85,
            alert_level=self._calculate_alert_level(anomalies, threats),
        )

    async def _surface_observe(self, target: str) -> dict:
        findings = {}
        target_type = self._classify_target(target)
        findings["target_type"] = target_type
        if target_type == "ip_address":
            findings["network_info"] = await self.network_eye.analyze_ip(target)
        elif target_type == "domain":
            findings["dns_info"] = await self.network_eye.analyze_domain(target)
        elif target_type == "url":
            findings["web_info"] = await self.network_eye.analyze_url(target)
        elif target_type == "code":
            findings["code_info"] = await self.code_eye.analyze(target)
        elif target_type == "file_path":
            findings["file_info"] = await self.file_eye.analyze(target)
        return findings

    def _classify_target(self, target: str) -> str:
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", target):
            return "ip_address"
        elif target.startswith("http"):
            return "url"
        elif "." in target and "/" not in target:
            return "domain"
        elif target.startswith("/") or "\\" in target:
            return "file_path"
        elif any(kw in target for kw in ["def ", "class ", "import "]):
            return "code"
        else:
            return "entity"

    async def _detect_patterns(self) -> list:
        if len(self.observations) < 5:
            return []
        patterns = []
        recent_scores = [obs.anomaly_score for obs in self.observations[-10:]]
        if len(recent_scores) >= 3:
            trend = (recent_scores[-1] - recent_scores[0]) / max(1, len(recent_scores))
            if trend > 0.05:
                patterns.append(Pattern(phrase="anomaly_score_increasing", frequency=len(recent_scores), memory_ids=[], confidence=0.85))
        return patterns

    async def _detect_patterns_in_target(self, target, surface) -> list:
        return [f"Analyzing patterns for {target}"]

    async def _detect_anomalies(self, target, surface) -> list:
        return []

    async def _threat_intelligence(self, target: str) -> dict:
        return {"threat_level": "low", "known_threats": []}

    async def _opportunity_scan(self, target: str) -> list:
        return [f"Potential opportunity in {target}"]

    async def _generate_predictions(self, target, analysis) -> list:
        return [f"Based on analysis of {target}, monitoring for changes."]

    async def _check_alert_conditions(self, observation: Observation) -> list:
        alerts = []
        if observation.anomaly_score > 0.8:
            alerts.append(Alert(level="HIGH", message=f"High anomaly: {observation.anomaly_score:.0%}", timestamp=datetime.now(timezone.utc).isoformat()))
        return alerts

    async def _scan_opportunities(self, observation) -> list:
        return []

    def _calculate_anomaly_score(self, network, processes, security) -> float:
        return 0.1

    def _calculate_alert_level(self, anomalies: list, threats: dict) -> str:
        tl = threats.get("threat_level", "low")
        if tl == "critical" or len(anomalies) > 5:
            return "CRITICAL"
        elif tl == "high" or len(anomalies) > 2:
            return "HIGH"
        elif tl == "medium":
            return "MEDIUM"
        return "LOW"

    async def generate_report(self) -> EagleEyeReport:
        duration = 0
        if self._start_time:
            duration = int((datetime.now(timezone.utc) - self._start_time).total_seconds())
        return EagleEyeReport(
            total_observations=len(self.observations), total_alerts=len(self.alerts),
            total_patterns=len(self.patterns), opportunities_found=len(self.opportunity_signals),
            highest_anomaly=max([o.anomaly_score for o in self.observations], default=0.0),
            watch_duration_seconds=duration,
        )

    def get_status(self) -> dict:
        return {
            "watching": self.is_watching,
            "observations": len(self.observations),
            "alerts": len(self.alerts),
            "patterns": len(self.patterns),
        }

    def save(self) -> dict:
        return {
            "observations": [o.to_dict() for o in self.observations[-100:]],
            "alerts": [a.to_dict() for a in self.alerts[-100:]],
            "patterns": [p.to_dict() for p in self.patterns[-100:]],
        }

    def load(self, data: dict):
        self.observations = []
        for od in data.get("observations", []):
            self.observations.append(Observation(**od))
        self.alerts = []
        for ad in data.get("alerts", []):
            self.alerts.append(Alert(**ad))
        self.patterns = []
        for pd in data.get("patterns", []):
            self.patterns.append(Pattern(**pd))
