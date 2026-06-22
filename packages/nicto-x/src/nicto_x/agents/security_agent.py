"""NICTO X — Security agent with real threat detection and vulnerability analysis."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from typing import Any, Optional
from nicto_x.agents.base import BaseAgent

logger = logging.getLogger("nicto_x.agents.security")


class SecurityAgent(BaseAgent):
    """Real threat detection, vulnerability analysis, and security auditing."""

    VULN_PATTERNS = {
        "sql_injection": [
            (r"(?i)(select\s+.+\s+from|insert\s+into|delete\s+from|drop\s+table|union\s+select)", "SQL injection pattern detected"),
            (r"(?i)('|\")\s*(or|and)\s*['\"].*['\"]", "SQL tautology injection"),
        ],
        "xss": [
            (r"(?i)<script[^>]*>.*?</script>", "XSS script tag"),
            (r"(?i)javascript\s*:", "XSS javascript protocol"),
            (r"(?i)onerror\s*=|onload\s*=|onclick\s*=", "XSS event handler"),
        ],
        "command_injection": [
            (r"(?i)(;\s*|\||`)\s*(rm|wget|curl|bash|sh|cmd|powershell)", "Command injection"),
            (r"(?i)\$\(.*\)", "Shell substitution injection"),
            (r"(?i)\$\{.*\}", "Shell variable injection"),
        ],
        "path_traversal": [
            (r"\.\./", "Directory traversal"),
            (r"\.\.\\", "Windows directory traversal"),
            (r"/etc/passwd", "Sensitive file access"),
        ],
        "insecure_code": [
            (r"(?i)eval\s*\(", "Dangerous eval() usage"),
            (r"(?i)exec\s*\(", "Dangerous exec() usage"),
            (r"(?i)pickle\.loads", "Insecure deserialization"),
            (r"(?i)assert\s+", "Assert statement (dangerous in production)"),
        ],
    }

    RISK_KEYWORDS = {
        "critical": ["remote code execution", "rce", "zero-day", "critical vulnerability", "cve-"],
        "high": ["sql injection", "xss", "authentication bypass", "privilege escalation"],
        "medium": ["information disclosure", "misconfiguration", "outdated", "weak encryption"],
        "low": ["missing header", "verbose error", "info leakage"],
    }

    PORT_SIGNATURES: dict[int, tuple[str, str]] = {
        21: ("FTP", "File Transfer Protocol"),
        22: ("SSH", "Secure Shell"),
        23: ("Telnet", "Telnet (unencrypted)"),
        25: ("SMTP", "Simple Mail Transfer"),
        53: ("DNS", "Domain Name System"),
        80: ("HTTP", "Hypertext Transfer Protocol"),
        110: ("POP3", "Post Office Protocol v3"),
        143: ("IMAP", "Internet Message Access Protocol"),
        443: ("HTTPS", "HTTP Secure"),
        445: ("SMB", "Server Message Block"),
        3306: ("MySQL", "MySQL Database"),
        3389: ("RDP", "Remote Desktop Protocol"),
        5432: ("PostgreSQL", "PostgreSQL Database"),
        6379: ("Redis", "Redis Key-Value Store"),
        8080: ("HTTP-Alt", "HTTP Alternate"),
        8443: ("HTTPS-Alt", "HTTPS Alternate"),
        27017: ("MongoDB", "MongoDB Database"),
    }

    async def execute(self, task: Any, context: Optional[dict] = None) -> dict:
        task_str = str(task)
        targets = self._extract_targets(task_str)
        findings = []
        risk_level = "low"
        risk_score = 0.0

        if targets:
            for target in targets:
                findings.extend(self._analyze_target(target, task_str))

        findings.extend(self._pattern_scan(task_str))

        if not findings:
            findings.extend(self._default_audit(task_str))

        risk_score = sum(f.get("severity", 0) for f in findings)
        if risk_score > 20:
            risk_level = "critical"
        elif risk_score > 10:
            risk_level = "high"
        elif risk_score > 3:
            risk_level = "medium"

        return {
            "agent": self.name,
            "task": task_str,
            "output": self._format_report(task_str, findings, risk_level),
            "findings": findings,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "targets_analyzed": targets if targets else ["task_description"],
        }

    def _extract_targets(self, text: str) -> list[str]:
        targets = []
        ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        domain_pattern = r"\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b"
        url_pattern = r"https?://[^\s]+"
        targets.extend(re.findall(ip_pattern, text))
        targets.extend(re.findall(domain_pattern, text))
        targets.extend(re.findall(url_pattern, text))
        return list(set(targets))

    def _analyze_target(self, target: str, context: str) -> list[dict]:
        findings = []
        if re.match(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", target):
            findings.append({
                "type": "network_target",
                "target": target,
                "detail": "IP address identified as potential target",
                "severity": 1,
                "recommendation": "Ensure firewall rules restrict access",
            })
            for port, (svc, desc) in self.PORT_SIGNATURES.items():
                for word in context.lower().split():
                    if svc.lower() in word or str(port) in word:
                        findings.append({
                            "type": "service_detection",
                            "target": target,
                            "service": svc,
                            "port": port,
                            "detail": f"{svc} ({desc}) mentioned in context",
                            "severity": 3 if port in [22, 3389, 3306, 5432, 6379, 27017] else 1,
                            "recommendation": f"Verify {svc} is properly secured",
                        })
        return findings

    def _pattern_scan(self, text: str) -> list[dict]:
        findings = []
        for vuln_type, patterns in self.VULN_PATTERNS.items():
            for pattern, desc in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    findings.append({
                        "type": vuln_type,
                        "detail": f"{desc}: {matches[0][:80] if isinstance(matches[0], str) else str(matches[0])[:80]}",
                        "severity": 5 if vuln_type in ["command_injection", "sql_injection"] else 3,
                        "recommendation": self._get_recommendation(vuln_type),
                    })

        for level, keywords in self.RISK_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text.lower():
                    sev = {"critical": 10, "high": 7, "medium": 4, "low": 1}
                    findings.append({
                        "type": f"risk_indicator_{level}",
                        "detail": f"Risk keyword '{kw}' detected",
                        "severity": sev.get(level, 1),
                        "recommendation": f"Investigate {level} risk indicator",
                    })
        return findings

    def _default_audit(self, text: str) -> list[dict]:
        checks = [
            ("ssl_tls", "Check SSL/TLS configuration", 2, "Use TLS 1.3 minimum"),
            ("authentication", "Verify authentication mechanism", 3, "Implement MFA"),
            ("encryption", "Check encryption at rest/transit", 2, "Use AES-256 for data at rest"),
            ("logging", "Verify audit logging is enabled", 1, "Enable comprehensive logging"),
            ("access_control", "Review access control policies", 3, "Apply least privilege principle"),
        ]
        return [
            {
                "type": check,
                "detail": desc,
                "severity": sev,
                "recommendation": rec,
            }
            for check, desc, sev, rec in checks
        ]

    def _get_recommendation(self, vuln_type: str) -> str:
        recs = {
            "sql_injection": "Use parameterized queries / prepared statements",
            "xss": "Sanitize user input, use Content-Security-Policy header",
            "command_injection": "Avoid shell commands; use safe APIs",
            "path_traversal": "Validate file paths, use allowlists",
            "insecure_code": "Never use eval/exec on untrusted data",
        }
        return recs.get(vuln_type, "Review and fix identified vulnerability")

    def _format_report(self, task: str, findings: list[dict], risk: str) -> str:
        lines = [f"Security Audit Report", f"Task: {task}", f"Risk Level: {risk.upper()}", f"Findings: {len(findings)}", ""]
        for f in findings:
            sev_tag = {"critical": "CRIT", "high": "HIGH", "medium": "MED", "low": "LOW"}
            tag = sev_tag.get(f.get("risk_level", risk), "INFO")
            lines.append(f"  [{tag}] {f.get('type', 'issue')}: {f.get('detail', '')[:100]}")
            if f.get("recommendation"):
                lines.append(f"         Fix: {f['recommendation']}")
        return "\n".join(lines)
