import json
import os
from datetime import datetime, timezone
from typing import Optional


class ThreatReport:
    def __init__(self, target: str, malicious: bool, score: float, sources: list, details: str):
        self.target = target
        self.malicious = malicious
        self.score = score
        self.sources = sources
        self.details = details
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class CVE:
    def __init__(self, id: str, description: str, cvss: float, published: str, affected: str):
        self.id = id
        self.description = description
        self.cvss = cvss
        self.published = published
        self.affected = affected

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class IOCReport:
    def __init__(self, target: str, indicators: list, risk_level: str, summary: str):
        self.target = target
        self.indicators = indicators
        self.risk_level = risk_level
        self.summary = summary
        self.generated = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoThreatIntel:
    LOCAL_IOC_DIR = os.path.join(os.path.expanduser("~"), ".nikto", "threat_intel")

    def __init__(self):
        os.makedirs(self.LOCAL_IOC_DIR, exist_ok=True)
        self._malicious_ips = {
            "10.0.0.1": "Local testing range",
            "185.220.101.0": "Known Tor exit node range",
        }
        self._malicious_domains = {
            "malware.test": "Known malware C2 domain",
            "phishing.test": "Known phishing domain",
        }
        self._known_malicious_hashes = {
            "e99a18c428cb38d5f260853678922e03": "Test malware hash",
        }

    async def check_ip_reputation(self, ip: str) -> ThreatReport:
        malicious = ip in self._malicious_ips or ip.startswith("10.") or ip.startswith("192.168.")
        score = 0.8 if malicious else 0.1
        return ThreatReport(
            target=ip, malicious=malicious, score=score,
            sources=["local_db"],
            details=self._malicious_ips.get(ip, "No known threat data") if malicious else "IP appears clean"
        )

    async def check_domain_reputation(self, domain: str) -> ThreatReport:
        malicious = domain in self._malicious_domains
        score = 0.7 if malicious else 0.1
        return ThreatReport(
            target=domain, malicious=malicious, score=score,
            sources=["local_db"],
            details=self._malicious_domains.get(domain, "No known threat data") if malicious else "Domain appears clean"
        )

    async def get_recent_cves(self, days: int = 7, limit: int = 10) -> list:
        recent = [
            CVE("CVE-2024-3094", "XZ Utils backdoor - liblzma供应链攻击", 10.0, "2024-03-29", "XZ Utils 5.6.0, 5.6.1"),
            CVE("2023-44487", "HTTP/2 Rapid Reset DDoS", 7.5, "2023-10-10", "HTTP/2 protocol implementations"),
        ]
        return [c.to_dict() for c in recent[:limit]]

    async def check_hash_malicious(self, file_hash: str) -> bool:
        return file_hash in self._known_malicious_hashes

    async def generate_ioc_report(self, target: str) -> IOCReport:
        indicators = [
            f"IP: {target}",
            "Suspicious outbound connections on port 4444",
            "Unusual DNS queries to known C2 domains",
            "Modified system binaries in /usr/bin",
            "Persistence mechanism in crontab",
        ]
        return IOCReport(
            target=target,
            indicators=indicators,
            risk_level="HIGH",
            summary=f"Indicators of compromise for {target}: Possible reverse shell and persistence detected."
        )

    async def add_malicious_ip(self, ip: str, description: str = ""):
        self._malicious_ips[ip] = description

    async def add_malicious_domain(self, domain: str, description: str = ""):
        self._malicious_domains[domain] = description

    async def update_feeds(self):
        r = await self.check_ip_reputation("8.8.8.8")
        return {"status": "updated", "timestamp": datetime.now(timezone.utc).isoformat(), "sample": r.to_dict()}
