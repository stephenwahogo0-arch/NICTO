import os
import json
from datetime import datetime, timezone
from typing import Optional


class Finding:
    def __init__(self, title: str, severity: str, description: str, remediation: str, cvss: float = 0.0):
        self.title = title
        self.severity = severity
        self.description = description
        self.remediation = remediation
        self.cvss = cvss

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class Report:
    def __init__(self, title: str, target: str, findings: list, summary: str):
        self.title = title
        self.target = target
        self.findings = findings
        self.summary = summary
        self.generated = datetime.now(timezone.utc).isoformat()
        self.version = "2.0"

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class CodeAudit:
    def __init__(self, files: list, issues: int, score: float):
        self.files = files
        self.issues = issues
        self.score = score

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoReportingEngine:
    async def generate_pentest_report(self, findings: list, target: str) -> Report:
        return Report(
            title="Penetration Test Report",
            target=target,
            findings=[f.to_dict() if isinstance(f, Finding) else f for f in findings],
            summary=f"Pentest report for {target} with {len(findings)} findings."
        )

    async def generate_code_audit_report(self, audit_results: CodeAudit) -> Report:
        return Report(
            title="Code Security Audit",
            target=audit_results.files[0] if audit_results.files else "unknown",
            findings=[{"file": f, "issues": audit_results.issues, "score": audit_results.score} for f in audit_results.files],
            summary=f"Audited {len(audit_results.files)} files. Score: {audit_results.score}/100."
        )

    async def generate_executive_summary(self, findings: list) -> str:
        critical = sum(1 for f in findings if isinstance(f, dict) and f.get("severity") == "critical")
        high = sum(1 for f in findings if isinstance(f, dict) and f.get("severity") == "high")
        medium = sum(1 for f in findings if isinstance(f, dict) and f.get("severity") == "medium")
        low = sum(1 for f in findings if isinstance(f, dict) and f.get("severity") == "low")
        return f"Executive Summary: {len(findings)} total findings ({critical} critical, {high} high, {medium} medium, {low} low). Immediate action required on critical and high severity items."

    async def export_to_pdf(self, report: Report, output_path: str) -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path.replace(".pdf", ".json"), "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        return output_path.replace(".pdf", ".json")

    async def export_to_html(self, report: Report, output_path: str) -> str:
        html = f"""<!DOCTYPE html>
<html><head><title>{report.title}</title>
<style>body {{ background:#000; color:#DCFCE7; font-family: monospace; }}
h1 {{ color:#00FF64; }}.finding {{ border:1px solid #00B43C; padding:1em; margin:1em 0; }}
.severity-critical {{ color:#FF4444; }}.severity-high {{ color:#FFB800; }}
</style></head><body>
<h1>{report.title}</h1>
<p>Target: {report.target}</p>
<p>Generated: {report.generated}</p>
<p>{report.summary}</p>
"""
        for f in report.findings:
            html += f'<div class="finding"><h3>{f.get("title", "Finding")}</h3><p>{f.get("description", "")}</p></div>\n'
        html += "</body></html>"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            f.write(html)
        return output_path
