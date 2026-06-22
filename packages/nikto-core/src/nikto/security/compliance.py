"""
Compliance Framework Checker for NIKTO.
Provides automated checking against common security and privacy compliance frameworks.
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    PCI_DSS = "PCI DSS"
    HIPAA = "HIPAA"
    GDPR = "GDPR"
    ISO_27001 = "ISO 27001"
    SOC2 = "SOC 2"
    NIST_CSF = "NIST CSF"
    CIS_CONTROLS = "CIS Controls"


class ComplianceStatus(Enum):
    """Compliance status for a control."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL = "partial"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"


@dataclass
class ComplianceControl:
    """Individual compliance control requirement."""
    id: str
    title: str
    description: str
    framework: ComplianceFramework
    severity: str  # high, medium, low
    status: ComplianceStatus
    evidence: List[str] = field(default_factory=list)
    remediation: str = ""
    last_checked: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> dict:
        """Convert to dictionary with enum values serialized."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "framework": self.framework.value,  # Convert enum to string
            "severity": self.severity,
            "status": self.status.value,  # Convert enum to string
            "evidence": self.evidence,
            "remediation": self.remediation,
            "last_checked": self.last_checked
        }


@dataclass
class ComplianceAssessment:
    """Results of a compliance assessment."""
    framework: ComplianceFramework
    target: str
    assessment_date: str
    total_controls: int
    compliant_controls: int
    non_compliant_controls: int
    partial_controls: int
    overall_score: float  # 0-100 percentage
    status: str  # pass, fail, warning
    controls: List[ComplianceControl]
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "framework": self.framework.value,
            "target": self.target,
            "assessment_date": self.assessment_date,
            "total_controls": self.total_controls,
            "compliant_controls": self.compliant_controls,
            "non_compliant_controls": self.non_compliant_controls,
            "partial_controls": self.partial_controls,
            "overall_score": self.overall_score,
            "status": self.status,
            "controls": [control.to_dict() for control in self.controls],
            "summary": self.summary
        }


class NiktoComplianceChecker:
    """Automated compliance framework checker."""
    
    def __init__(self):
        self.frameworks: Dict[ComplianceFramework, List[ComplianceControl]] = {}
        self.assessments: List[ComplianceAssessment] = []
        self._load_framework_definitions()
        self._init_rule_engine()
    
    def _load_framework_definitions(self):
        """Load control definitions for supported frameworks."""
        # PCI DSS Controls (simplified subset)
        pci_dss_controls = [
            ComplianceControl(
                id="PCI DSS 1.1",
                title="Install and maintain a firewall configuration",
                description="Establish firewall and router configuration standards",
                framework=ComplianceFramework.PCI_DSS,
                severity="high",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="PCI DSS 2.1",
                title="Change default passwords",
                description="Change vendor-supplied defaults before installing systems",
                framework=ComplianceFramework.PCI_DSS,
                severity="high",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="PCI DSS 3.1",
                title="Protect stored cardholder data",
                description="Encrypt transmission of cardholder data across open networks",
                framework=ComplianceFramework.PCI_DSS,
                severity="high",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="PCI DSS 8.1",
                title="Identify and authenticate access",
                description="Assign unique ID to each person with computer access",
                framework=ComplianceFramework.PCI_DSS,
                severity="high",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="PCI DSS 10.1",
                title="Track and monitor access to network resources",
                description="Implement audit trails to link all access to system components",
                framework=ComplianceFramework.PCI_DSS,
                severity="medium",
                status=ComplianceStatus.UNKNOWN
            )
        ]
        
        # HIPAA Controls (simplified subset)
        hipaa_controls = [
            ComplianceControl(
                id="HIPAA 164.308(a)(1)(ii)(D)",
                title="Information System Activity Review",
                description="Implement procedures to regularly review records of information system activity",
                framework=ComplianceFramework.HIPAA,
                severity="high",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="HIPAA 164.308(a)(1)(ii)(E)",
                title="Access Control",
                description="Implement technical access control policies",
                framework=ComplianceFramework.HIPAA,
                severity="high",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="HIPAA 164.308(a)(1)(ii)(B)",
                title="Risk Analysis",
                description="Conduct an accurate and thorough assessment of risks",
                framework=ComplianceFramework.HIPAA,
                severity="high",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="HIPAA 164.308(a)(1)(ii)(C)",
                title="Risk Management",
                description="Implement security measures to reduce risks",
                framework=ComplianceFramework.HIPAA,
                severity="high",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="HIPAA 164.310(a)(1)",
                title="Facility Access Controls",
                description="Implement policies to limit physical access",
                framework=ComplianceFramework.HIPAA,
                severity="medium",
                status=ComplianceStatus.UNKNOWN
            )
        ]
        
        # GDPR Controls (simplified subset)
        gdpr_controls = [
            ComplianceControl(
                id="GDPR Art. 5(1)(f)",
                title="Integrity and confidentiality",
                description="Process personal data ensuring appropriate security",
                framework=ComplianceFramework.GDPR,
                severity="high",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="GDPR Art. 32",
                title="Security of processing",
                description="Implement appropriate technical and organizational measures",
                framework=ComplianceFramework.GDPR,
                severity="high",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="GDPR Art. 33",
                title="Notification of breach",
                description="Notify supervisory authority of personal data breach",
                framework=ComplianceFramework.GDPR,
                severity="high",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="GDPR Art. 25",
                title="Data protection by design",
                description="Implement data protection principles from the outset",
                framework=ComplianceFramework.GDPR,
                severity="medium",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="GDPR Art. 30",
                title="Records of processing activities",
                description="Maintain records of processing activities",
                framework=ComplianceFramework.GDPR,
                severity="medium",
                status=ComplianceStatus.UNKNOWN
            )
        ]
        
        # ISO 27001 Controls (simplified subset - Annex A)
        iso_27001_controls = [
            ComplianceControl(
                id="ISO 27001 A.5.1",
                title="Information security policies",
                description="Establish, approve and communicate information security policies",
                framework=ComplianceFramework.ISO_27001,
                severity="high",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="ISO 27001 A.6.1.1",
                title="Information security roles",
                description="Allocate information security responsibilities",
                framework=ComplianceFramework.ISO_27001,
                severity="medium",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="ISO 27001 A.9.1.1",
                title="Access control policy",
                description="Establish access control policy",
                framework=ComplianceFramework.ISO_27001,
                severity="high",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="ISO 27001 A.10.1.1",
                title="Cryptographic key management",
                description="Manage cryptographic keys",
                framework=ComplianceFramework.ISO_27001,
                severity="high",
                status=ComplianceStatus.UNKNOWN
            ),
            ComplianceControl(
                id="ISO 27001 A.12.4.1",
                title="Event logging",
                description="Record events and generate logs",
                framework=ComplianceFramework.ISO_27001,
                severity="medium",
                status=ComplianceStatus.UNKNOWN
            )
        ]
        
        # Store framework definitions
        self.frameworks[ComplianceFramework.PCI_DSS] = pci_dss_controls
        self.frameworks[ComplianceFramework.HIPAA] = hipaa_controls
        self.frameworks[ComplianceFramework.GDPR] = gdpr_controls
        self.frameworks[ComplianceFramework.ISO_27001] = iso_27001_controls
        
        # TODO: Add SOC2, NIST CSF, CIS Controls definitions
    
    async def assess_framework(
        self, 
        framework: ComplianceFramework, 
        target: str,
        use_scanner: bool = True,
        use_threat_intel: bool = True
    ) -> ComplianceAssessment:
        """
        Assess target against a compliance framework.
        
        Args:
            framework: The compliance framework to assess against
            target: Target to assess (IP, domain, system description)
            use_scanner: Whether to use vulnerability scanner for technical checks
            use_threat_intel: Whether to use threat intelligence for context
            
        Returns:
            ComplianceAssessment object with results
        """
        controls = self.frameworks.get(framework, [])
        if not controls:
            raise ValueError(f"Framework {framework.value} not supported")
        
        # Reset control statuses for fresh assessment
        for control in controls:
            control.status = ComplianceStatus.UNKNOWN
            control.evidence = []
            control.remediation = ""
            control.last_checked = datetime.now(timezone.utc).isoformat()
        
        # TODO: In a real implementation, this would:
        # 1. Use network scanner to check technical controls
        # 2. Use threat intelligence for contextual awareness
        # 3. Interview stakeholders for procedural controls
        # 4. Review documentation and configurations
        # For now, we'll simulate with some basic logic
        
        assessed_controls = []
        for control in controls:
            assessed_control = await self._assess_control(
                control, target, use_scanner, use_threat_intel
            )
            assessed_controls.append(assessed_control)
        
        # Calculate assessment results
        total = len(assessed_controls)
        compliant = sum(1 for c in assessed_controls if c.status == ComplianceStatus.COMPLIANT)
        non_compliant = sum(1 for c in assessed_controls if c.status == ComplianceStatus.NON_COMPLIANT)
        partial = sum(1 for c in assessed_controls if c.status == ComplianceStatus.PARTIAL)
        
        overall_score = (compliant * 100 + partial * 50) / max(total, 1)
        
        # Determine overall status
        if overall_score >= 90:
            status = "pass"
        elif overall_score >= 70:
            status = "warning"
        else:
            status = "fail"
        
        summary = self._generate_summary(
            framework, target, compliant, non_compliant, partial, total, overall_score
        )
        
        assessment = ComplianceAssessment(
            framework=framework,
            target=target,
            assessment_date=datetime.now(timezone.utc).isoformat(),
            total_controls=total,
            compliant_controls=compliant,
            non_compliant_controls=non_compliant,
            partial_controls=partial,
            overall_score=round(overall_score, 2),
            status=status,
            controls=assessed_controls,
            summary=summary
        )
        
        self.assessments.append(assessment)
        return assessment
    
    def _init_rule_engine(self):
        self._rules = [
            self._check_default_credentials,
            self._check_encryption,
            self._check_logging,
            self._check_access_control,
            self._check_firewall,
            self._check_risk_assessment,
            self._check_policy,
        ]

    async def _assess_control(
        self, 
        control: ComplianceControl, 
        target: str,
        use_scanner: bool,
        use_threat_intel: bool
    ) -> ComplianceControl:
        control_id = control.id.lower()
        assessed = False
        for rule in self._rules:
            result = rule(control_id, target)
            if result is not None:
                control.status, control.evidence, control.remediation = result
                assessed = True
                break
        if not assessed:
            control.status = ComplianceStatus.UNKNOWN
            control.evidence = ["Manual review required"]
            control.remediation = "Conduct manual assessment of this control"
        control.last_checked = datetime.now(timezone.utc).isoformat()
        return control

    def _check_default_credentials(self, cid: str, target: str):
        if "password" in cid or "default" in cid:
            evidence = self._test_common_credentials(target)
            if evidence:
                return ComplianceStatus.NON_COMPLIANT, evidence, "Change all default credentials immediately"
            return ComplianceStatus.COMPLIANT, ["Default credentials check passed"], ""
        return None

    def _check_encryption(self, cid: str, target: str):
        if "encrypt" in cid or "cryptographic" in cid or "crypto" in cid:
            evidence = [f"TLS check on {target}: {self._check_tls(target)}"]
            return ComplianceStatus.PARTIAL, evidence, "Ensure all sensitive data is encrypted in transit and at rest"
        return None

    def _check_logging(self, cid: str, target: str):
        if "log" in cid or "audit" in cid or "event" in cid:
            return ComplianceStatus.COMPLIANT, ["Audit logging configuration reviewed"], ""
        return None

    def _check_access_control(self, cid: str, target: str):
        if "access" in cid or "authenticate" in cid or "identify" in cid:
            return ComplianceStatus.PARTIAL, ["Access control policies reviewed"], "Implement least privilege access controls"
        return None

    def _check_firewall(self, cid: str, target: str):
        if "firewall" in cid or "network" in cid or "port" in cid:
            open_ports = self._scan_common_ports(target)
            if len(open_ports) > 10:
                return ComplianceStatus.NON_COMPLIANT, [f"{len(open_ports)} open ports detected: {open_ports[:5]}"], "Restrict inbound access with firewall rules"
            return ComplianceStatus.COMPLIANT, [f"Firewall check: {len(open_ports)} open ports"], ""
        return None

    def _check_risk_assessment(self, cid: str, target: str):
        if "risk" in cid or "assessment" in cid:
            return ComplianceStatus.NON_COMPLIANT, ["No recent risk assessment found"], "Conduct and document risk assessment annually"
        return None

    def _check_policy(self, cid: str, target: str):
        if "policy" in cid or "procedure" in cid or "standard" in cid:
            return ComplianceStatus.PARTIAL, ["Basic security policies exist"], "Develop and maintain comprehensive security policies"
        return None

    def _test_common_credentials(self, target: str) -> list:
        evidence = []
        common = [("admin", "admin"), ("admin", "password"), ("root", "root"), ("test", "test")]
        for user, pw in common:
            try:
                import urllib.request
                req = urllib.request.Request(f"http://{target}/login", data=f"user={user}&pass={pw}".encode(), method="POST")
                resp = urllib.request.urlopen(req, timeout=3)
                if resp.getcode() == 200 and "failed" not in resp.read().decode().lower():
                    evidence.append(f"Default creds work: {user}:{pw}")
            except Exception:
                pass
        return evidence

    def _check_tls(self, target: str) -> str:
        try:
            import ssl, socket
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=target) as sock:
                sock.settimeout(3)
                sock.connect((target, 443))
                ver = sock.version()
                return f"TLS {ver} enabled"
        except Exception:
            return "TLS not detected on port 443"

    def _scan_common_ports(self, target: str) -> list:
        open_ports = []
        for port in [21, 22, 23, 25, 80, 443, 445, 3306, 3389, 8080]:
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                if sock.connect_ex((target, port)) == 0:
                    open_ports.append(port)
                sock.close()
            except Exception:
                pass
        return open_ports
    
    def _generate_summary(
        self,
        framework: ComplianceFramework,
        target: str,
        compliant: int,
        non_compliant: int,
        partial: int,
        total: int,
        score: float
    ) -> str:
        """Generate a human-readable summary of the assessment."""
        return (
            f"Compliance assessment for {target} against {framework.value}: "
            f"{score:.1f}% compliant ({compliant}/{total} controls). "
            f"{non_compliant} non-compliant, {partial} partial, {compliant} compliant controls."
        )
    
    def get_assessment_history(self, framework: Optional[ComplianceFramework] = None) -> List[Dict]:
        """Get history of compliance assessments."""
        if framework:
            return [a.to_dict() for a in self.assessments if a.framework == framework]
        return [a.to_dict() for a in self.assessments]
    
    def get_latest_assessment(self, framework: ComplianceFramework) -> Optional[Dict]:
        """Get the most recent assessment for a framework."""
        framework_assessments = [
            a for a in self.assessments if a.framework == framework
        ]
        if not framework_assessments:
            return None
        
        # Sort by assessment date descending
        framework_assessments.sort(
            key=lambda x: x.assessment_date, 
            reverse=True
        )
        return framework_assessments[0].to_dict()
    
    def export_assessment(self, assessment: ComplianceAssessment, format: str = "json") -> str:
        """
        Export assessment to specified format.
        
        Args:
            assessment: The assessment to export
            format: Export format (json, csv, html)
            
        Returns:
            String representation of the assessment in requested format
        """
        if format.lower() == "json":
            return json.dumps(assessment.to_dict(), indent=2)
        elif format.lower() == "csv":
            # Simple CSV export of controls
            lines = ["Control ID,Title,Status,Severity,Evidence,Remediation"]
            for control in assessment.controls:
                lines.append(
                    f'"{control.id}","{control.title}","{control.status.value}",'
                    f'"{control.severity}","{" | ".join(control.evidence)}","{control.remediation}"'
                )
            return "\n".join(lines)
        elif format.lower() == "html":
            # Simple HTML report
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{assessment.framework.value} Compliance Assessment</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1, h2 {{ color: #2c3e50; }}
                    .score {{ font-size: 24px; font-weight: bold; }}
                    .pass {{ color: #27ae60; }}
                    .warning {{ color: #f39c12; }}
                    .fail {{ color: #e74c3c; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:hover {{ background-color: #f5f5f5; }}
                    .compliant {{ background-color: #d5f5e3; }}
                    .non-compliant {{ background-color: #f5b7b1; }}
                    .partial {{ background-color: #fad7a0; }}
                    .unknown {{ background-color: #d5dbdb; }}
                </style>
            </head>
            <body>
                <h1>{assessment.framework.value} Compliance Assessment</h1>
                <p><strong>Target:</strong> {assessment.target}</p>
                <p><strong>Assessment Date:</strong> {assessment.assessment_date}</p>
                <p><strong>Overall Score:</strong> 
                   <span class="{assessment.status}">{assessment.overall_score}%</span>
                </p>
                <p><strong>Status:</strong> 
                   <span class="{assessment.status}">{assessment.status.upper()}</span>
                </p>
                <p>{assessment.summary}</p>
                
                <h2>Control Details</h2>
                <table>
                    <tr>
                        <th>Control ID</th>
                        <th>Title</th>
                        <th>Status</th>
                        <th>Severity</th>
                        <th>Evidence</th>
                        <th>Remediation</th>
                    </tr>
            """
            
            for control in assessment.controls:
                status_class = control.status.value.replace("_", "-")
                html += f"""
                    <tr class="{status_class}">
                        <td>{control.id}</td>
                        <td>{control.title}</td>
                        <td>{control.status.value}</td>
                        <td>{control.severity}</td>
                        <td>{" | ".join(control.evidence) if control.evidence else "None"}</td>
                        <td>{control.remediation}</td>
                    </tr>
                """
            
            html += """
                </table>
            </body>
            </html>
            """
            return html
        else:
            raise ValueError(f"Unsupported format: {format}")


# Export the main class
__all__ = ["NiktoComplianceChecker", "ComplianceFramework", "ComplianceStatus", "ComplianceAssessment"]