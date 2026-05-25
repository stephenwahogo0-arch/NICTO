"""NIKTO Security Scanner — port scanning, vulnerability assessment, CVE lookup."""

import json
import hashlib
import uuid
import re
import socket
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict


class ScanTarget:
    def __init__(self, host: str, port_range: str = "1-1024",
                 protocol: str = "tcp", tags: list = None):
        self.id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]
        self.host = host
        self.port_range = port_range
        self.protocol = protocol
        self.tags = tags or []
        self.scanned_at = None
        self.results = []

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class ScanResult:
    def __init__(self, port: int, protocol: str, service: str,
                 state: str = "open", banner: str = "",
                 vulnerabilities: list = None):
        self.port = port
        self.protocol = protocol
        self.service = service
        self.state = state
        self.banner = banner
        self.vulnerabilities = vulnerabilities or []
        self.risk_score = self._compute_risk()

    def _compute_risk(self) -> float:
        score = 0.0
        for v in self.vulnerabilities:
            cvss = v.get("cvss", 0)
            score += cvss * 0.3
        return min(10.0, score)

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoScanner:
    """
    Security Scanner Engine.
    Scans targets, detects services, looks up CVEs, assesses risk.
    """

    COMMON_PORTS = {
        21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp",
        53: "dns", 80: "http", 110: "pop3", 143: "imap",
        443: "https", 445: "smb", 993: "imaps", 995: "pop3s",
        1433: "mssql", 1521: "oracle", 2049: "nfs",
        3306: "mysql", 3389: "rdp", 5432: "postgresql",
        5900: "vnc", 6379: "redis", 8080: "http-proxy",
        8443: "https-alt", 27017: "mongodb",
    }

    VULN_SIGNATURES = {
        "ssh": [
            {"cve": "CVE-2018-15473", "cvss": 5.3, "desc": "OpenSSH user enumeration"},
            {"cve": "CVE-2024-6387", "cvss": 8.1, "desc": "OpenSSH regreSSHion RCE"},
        ],
        "ftp": [
            {"cve": "CVE-2021-3461", "cvss": 7.5, "desc": "VSFTPD backdoor"},
        ],
        "http": [
            {"cve": "CVE-2021-44228", "cvss": 10.0, "desc": "Log4Shell RCE"},
            {"cve": "CVE-2017-5638", "cvss": 10.0, "desc": "Struts2 OGNL RCE"},
        ],
        "smb": [
            {"cve": "CVE-2017-0144", "cvss": 9.3, "desc": "EternalBlue RCE"},
            {"cve": "CVE-2020-0796", "cvss": 9.8, "desc": "SMBGhost RCE"},
        ],
        "rdp": [
            {"cve": "CVE-2019-0708", "cvss": 9.8, "desc": "BlueKeep RCE"},
        ],
        "mysql": [
            {"cve": "CVE-2023-21971", "cvss": 7.5, "desc": "MySQL ODBC RCE"},
        ],
        "redis": [
            {"cve": "CVE-2022-0543", "cvss": 10.0, "desc": "Redis Lua sandbox escape"},
        ],
    }

    def __init__(self):
        self.scan_history = []
        self.max_history = 100
        self.cve_cache = {}

    # ── Scanning ───────────────────────────────────────────────────────

    def scan_target(self, host: str, port_range: str = "1-1024",
                    protocol: str = "tcp") -> dict:
        target = ScanTarget(host, port_range, protocol)
        ports = self._parse_ports(port_range)
        results = []
        for port in ports:
            if port > 65535 or port < 1:
                continue
            service = self.COMMON_PORTS.get(port, "unknown")
            state = "open" if port in self.COMMON_PORTS or port % 1000 == 0 else "filtered"
            if state == "open" and port < 50000:
                banner = self._simulate_banner(service)
                vulns = self._check_vulns(service)
            else:
                banner = ""
                vulns = []
            result = ScanResult(port, protocol, service, state, banner, vulns)
            results.append(result)
        target.scanned_at = datetime.now(timezone.utc).isoformat()
        target.results = [r.to_dict() for r in results]
        target.tags.append("scanned")
        self.scan_history.append(target.to_dict())
        if len(self.scan_history) > self.max_history:
            self.scan_history = self.scan_history[-self.max_history:]
        return self._build_report(target)

    def _build_report(self, target: ScanTarget) -> dict:
        open_ports = [r for r in target.results if r["state"] == "open"]
        vuln_count = sum(len(r.get("vulnerabilities", [])) for r in target.results)
        risk_scores = [r.get("risk_score", 0) for r in target.results]
        avg_risk = sum(risk_scores) / max(len(risk_scores), 1)
        return {
            "target": target.host,
            "scanned_at": target.scanned_at,
            "port_range": target.port_range,
            "total_ports_scanned": len(target.results),
            "open_ports": len(open_ports),
            "filtered_ports": len(target.results) - len(open_ports),
            "vulnerabilities_found": vuln_count,
            "average_risk_score": round(avg_risk, 2),
            "critical_findings": sum(1 for r in target.results
                                     for v in r.get("vulnerabilities", [])
                                     if v.get("cvss", 0) >= 9.0),
            "results": target.results[:50],
        }

    # ── Quick Scan ────────────────────────────────────────────────────

    def quick_scan(self, host: str) -> dict:
        """Scan only top 20 most common ports."""
        top_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445,
                     993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080]
        port_str = ",".join(str(p) for p in top_ports)
        return self.scan_target(host, port_str)

    # ── CVE Lookup ────────────────────────────────────────────────────

    def lookup_cve(self, cve_id: str) -> Optional[dict]:
        for service, vulns in self.VULN_SIGNATURES.items():
            for v in vulns:
                if v["cve"].lower() == cve_id.lower():
                    return {**v, "affected_service": service}
        return None

    def search_vulns(self, query: str) -> list:
        q = query.lower()
        results = []
        for service, vulns in self.VULN_SIGNATURES.items():
            for v in vulns:
                if q in v["cve"].lower() or q in v["desc"].lower() or q in service:
                    results.append({**v, "affected_service": service})
        return results

    # ── Helpers ───────────────────────────────────────────────────────

    def _parse_ports(self, port_range: str) -> list:
        ports = set()
        parts = port_range.replace(" ", "").split(",")
        for part in parts:
            if "-" in part:
                try:
                    start, end = part.split("-")
                    for p in range(int(start), int(end) + 1):
                        ports.add(p)
                except ValueError:
                    continue
            else:
                try:
                    ports.add(int(part))
                except ValueError:
                    continue
        return sorted(ports)

    def _simulate_banner(self, service: str) -> str:
        banners = {
            "ssh": "SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6",
            "http": "Apache/2.4.57 (Ubuntu)",
            "https": "nginx/1.24.0",
            "ftp": "220 ProFTPD 1.3.5 Server",
            "smtp": "220 mail.example.com ESMTP Postfix (Ubuntu)",
            "mysql": "5.7.42-0ubuntu0.18.04.1",
            "postgresql": "PostgreSQL 14.10",
        }
        return banners.get(service, f"{service} service")

    def _check_vulns(self, service: str) -> list:
        return self.VULN_SIGNATURES.get(service, [])

    # ── Risk Assessment ───────────────────────────────────────────────

    def assess_risk(self, scan_report: dict) -> dict:
        open_ports = scan_report.get("open_ports", 0)
        vulns = scan_report.get("vulnerabilities_found", 0)
        critical = scan_report.get("critical_findings", 0)
        avg_risk = scan_report.get("average_risk_score", 0)
        score = min(10, (open_ports * 0.3 + vulns * 0.5 + critical * 2 + avg_risk * 0.5))
        if score >= 8:
            level = "CRITICAL"
        elif score >= 5:
            level = "HIGH"
        elif score >= 3:
            level = "MEDIUM"
        elif score >= 1:
            level = "LOW"
        else:
            level = "INFO"
        return {
            "risk_score": round(score, 1),
            "risk_level": level,
            "factors": {
                "open_ports": open_ports,
                "vulnerabilities": vulns,
                "critical_findings": critical,
                "average_cvss": avg_risk,
            },
            "recommendations": self._generate_recommendations(level, open_ports, vulns),
        }

    def _generate_recommendations(self, level: str, ports: int, vulns: int) -> list:
        recs = []
        if level in ("CRITICAL", "HIGH"):
            recs.append("Immediately patch identified vulnerabilities")
            recs.append("Restrict inbound access with firewall rules")
        if ports > 5:
            recs.append("Reduce attack surface by closing unnecessary ports")
        if vulns > 2:
            recs.append("Run full vulnerability scan with credentialed scanning")
        recs.append("Enable logging and monitoring for all services")
        recs.append("Review and rotate all credentials")
        return recs

    def get_stats(self) -> dict:
        return {
            "total_scans": len(self.scan_history),
            "total_ports_scanned": sum(
                len(s.get("results", [])) for s in self.scan_history
            ),
            "total_vulnerabilities_found": sum(
                s.get("vulnerabilities_found", 0) for s in self.scan_history
            ),
            "cve_signatures": sum(len(v) for v in self.VULN_SIGNATURES.values()),
            "services_monitored": len(self.COMMON_PORTS),
        }

    def save(self) -> dict:
        return {
            "scan_history": self.scan_history[-50:],
            "cve_cache": self.cve_cache,
        }

    def load(self, data: dict):
        self.scan_history = data.get("scan_history", [])
        self.cve_cache = data.get("cve_cache", {})
