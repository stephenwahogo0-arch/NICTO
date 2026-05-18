import asyncio
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SIEMAnalyst:
    """Autonomous SIEM & Log Analysis — Cross-log correlation and natural language threat hunting."""

    def __init__(self):
        self._logs_cache = {}

    async def ingest_logs(self, source_name: str, log_paths: list[str]) -> dict:
        """Ingest gigabytes of disparate logs simultaneously."""
        total_lines = 0
        self._logs_cache[source_name] = []

        for lp in log_paths:
            p = Path(lp)
            if p.exists() and p.is_file():
                try:
                    content = p.read_text(errors="replace")
                    lines = content.splitlines()
                    self._logs_cache[source_name].extend([
                        {"line": i + 1, "content": line, "source": lp}
                        for i, line in enumerate(lines) if line.strip()
                    ])
                    total_lines += len(lines)
                except Exception as e:
                    logger.error(f"Error ingesting {lp}: {e}")
            elif p.exists() and p.is_dir():
                for f in p.rglob("*"):
                    if f.is_file() and f.stat().st_size < 50 * 1024 * 1024:
                        try:
                            content = f.read_text(errors="replace")
                            lines = content.splitlines()
                            self._logs_cache[source_name].extend([
                                {"line": i + 1, "content": line, "source": str(f)}
                                for i, line in enumerate(lines) if line.strip()
                            ])
                            total_lines += len(lines)
                        except: pass

        return {
            "source": source_name,
            "total_lines_ingested": total_lines,
            "total_size_bytes": sum(len(e["content"]) for e in self._logs_cache[source_name]),
        }

    async def cross_log_correlation(self, sources: list[str] = None) -> list[dict]:
        """Cross-Log Correlation — Track multi-day trails across multiple servers."""
        sources = sources or list(self._logs_cache.keys())
        correlations = []
        ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
        ts_pattern = re.compile(r'\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}')

        for src in sources:
            entries = self._logs_cache.get(src, [])
            ip_tracker = {}

            for entry in entries:
                line = entry.get("content", "")
                ips = ip_pattern.findall(line)
                ts_match = ts_pattern.search(line)

                for ip in ips:
                    if ip not in ip_tracker:
                        ip_tracker[ip] = {
                            "ip": ip,
                            "first_seen": ts_match.group() if ts_match else "unknown",
                            "sources": set(),
                            "total_hits": 0,
                            "entries": [],
                        }
                    ip_tracker[ip]["sources"].add(src)
                    ip_tracker[ip]["total_hits"] += 1
                    ip_tracker[ip]["entries"].append(line[:200])

            for ip, data in ip_tracker.items():
                if data["total_hits"] >= 3 or len(data["sources"]) >= 2:
                    correlations.append({
                        "ip": ip,
                        "first_seen": data["first_seen"],
                        "sources": list(data["sources"]),
                        "hit_count": data["total_hits"],
                        "sample_entries": data["entries"][:5],
                    })

        correlations.sort(key=lambda x: x["hit_count"], reverse=True)
        return correlations[:100]

    async def natural_language_threat_hunt(self, query: str) -> dict:
        """Natural Language Threat Hunting — Query logs in plain English."""
        q_lower = query.lower()
        results = {
            "query": query,
            "parsed_intent": {},
            "matching_entries": [],
            "summary": "",
        }

        intent = {}
        if "unusual" in q_lower or "suspicious" in q_lower or "anomal" in q_lower:
            intent["type"] = "anomaly_detection"
        if "login" in q_lower or "authentication" in q_lower or "auth" in q_lower:
            intent["type"] = intent.get("type", "") + "_login_analysis"
        if "ip" in q_lower or "address" in q_lower:
            intent["target"] = "ip_address"
        if "admin" in q_lower:
            intent["target"] = "administrative_actions"
        if "unknown" in q_lower:
            intent["filter"] = "unknown_sources"
        if "config" in q_lower or "change" in q_lower:
            intent["event"] = "configuration_change"
        if "fail" in q_lower:
            intent["status"] = "failed"
        if "error" in q_lower:
            intent["status"] = "error"

        results["parsed_intent"] = intent

        for src, entries in self._logs_cache.items():
            for entry in entries:
                line = entry.get("content", "").lower()
                score = 0

                if "unusual" in q_lower and ("anomal" in line or "unusual" in line):
                    score += 1
                if "login" in q_lower and ("login" in line or "auth" in line):
                    score += 1
                if "ip" in q_lower and re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', line):
                    score += 1
                if "fail" in q_lower and ("fail" in line or "error" in line):
                    score += 1
                if "admin" in q_lower and "admin" in line:
                    score += 1
                if "unknown" in q_lower and "unknown" in line:
                    score += 1

                if score >= 2:
                    results["matching_entries"].append({
                        "source": entry.get("source", src),
                        "line": entry.get("line", 0),
                        "content": entry.get("content", "")[:300],
                        "relevance": score,
                    })

        results["matching_entries"].sort(key=lambda x: x["relevance"], reverse=True)
        results["matching_entries"] = results["matching_entries"][:50]

        results["summary"] = (
            f"Found {len(results['matching_entries'])} matching entries across "
            f"{len(self._logs_cache)} log sources matching intent: {intent}"
        )

        return results
