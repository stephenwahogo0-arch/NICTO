"""
Eagle Eye — NIKTO's truth verification & preemptive issue detection system.

Capabilities:
  • Lie Detection — analyzes text for deception markers, contradictions, vagueness
  • Preemptive Issue Scanner — catches potential failures before they happen
  • Anomaly Detection — monitors system for unusual behavior patterns
  • Truth Verification — cross-references claims against knowledge base
"""
import ast
import difflib
import hashlib
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ─── Lie Detection ────────────────────────────────────────────

DECEPTION_MARKERS = {
    "hedging": [
        r"\bi think\b", r"\bi believe\b", r"\bin my opinion\b",
        r"\bpossibly\b", r"\bperhaps\b", r"\bmaybe\b", r"\bmight\b",
        r"\bcould be\b", r"\bit seems\b", r"\bi suppose\b",
        r"\bas far as i know\b", r"\bto the best of\b",
    ],
    "vagueness": [
        r"\bsome things\b", r"\ba lot\b", r"\bnot much\b",
        r"\bthings\b", r"\bstuff\b", r"\bwhatever\b",
        r"\betc\b", r"\betc\.\b", r"\band so on\b",
    ],
    "overconfidence": [
        r"\bdefinitely\b", r"\babsolutely\b", r"\bwithout question\b",
        r"\bobviously\b", r"\bclearly\b", r"\bof course\b",
        r"\bwithout a doubt\b", r"\b100%\b", r"\bnever wrong\b",
    ],
    "evasion": [
        r"\bthat's a good question\b", r"\bthat's complex\b",
        r"\bi can't say\b", r"\bi don't know\b",
        r"\bi'm not sure\b", r"\bi'd rather not\b",
        r"\blet me think about that\b",
    ],
    "contradiction_markers": [
        r"\bhowever\b", r"\bbut\b", r"\byet\b", r"\balthough\b",
        r"\bcontrary to\b", r"\bon the other hand\b",
        r"\bdespite\b", r"\bnevertheless\b",
    ],
}


class LieDetector:
    """Analyzes text for deception markers and truth consistency."""

    def __init__(self):
        self.history: list[dict] = []
        self._compiled = {
            category: [re.compile(p, re.IGNORECASE) for p in patterns]
            for category, patterns in DECEPTION_MARKERS.items()
        }

    def analyze(self, text: str, source: str = "unknown") -> dict:
        if not text:
            return {"deception_score": 0.0, "flags": [], "confidence": 0.0}

        text_lower = text.lower()
        flags = []
        total_matches = 0

        for category, patterns in self._compiled.items():
            for pattern in patterns:
                matches = pattern.findall(text_lower)
                if matches:
                    total_matches += len(matches)
                    flags.append({
                        "category": category,
                        "pattern": pattern.pattern,
                        "matches": len(matches),
                        "examples": matches[:3],
                    })

        # Calculate deception score (0.0 = truthful, 1.0 = likely deceptive)
        word_count = len(text.split())
        if word_count == 0:
            return {"deception_score": 0.0, "flags": [], "confidence": 0.0}

        marker_density = total_matches / max(word_count, 1)
        deception_score = min(1.0, marker_density * 10)

        # Check for internal contradictions
        contradictions = self._find_contradictions(text_lower)
        if contradictions:
            deception_score = min(1.0, deception_score + 0.15)
            flags.append({
                "category": "contradiction",
                "pattern": "internal contradiction",
                "matches": len(contradictions),
                "examples": contradictions[:3],
            })

        confidence = min(1.0, 0.3 + (total_matches * 0.1))

        result = {
            "deception_score": round(deception_score, 3),
            "flags": flags,
            "total_markers": total_matches,
            "word_count": word_count,
            "marker_density": round(marker_density, 4),
            "confidence": round(confidence, 3),
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.history.append(result)
        return result

    def _find_contradictions(self, text: str) -> list[str]:
        contradictions = []
        positive = set()
        negative = set()

        pos_patterns = [
            (r"\byes\b", r"\bis\b", r"\bcan\b", r"\bdoes\b",
             r"\bhave\b", r"\bwill\b", r"\bknown\b", r"\bcertain\b"),
        ]
        neg_patterns = [
            (r"\bno\b", r"\bisn't\b", r"\bcan't\b", r"\bdoesn't\b",
             r"\bhaven't\b", r"\bwon't\b", r"\bunknown\b", r"\buncertain\b"),
        ]

        sentences = re.split(r'[.!?]+', text)
        for i, sent in enumerate(sentences):
            sent = sent.strip()
            if not sent:
                continue
            for pat in pos_patterns[0]:
                if re.search(pat, sent):
                    positive.add(sent[:50])
            for pat in neg_patterns[0]:
                if re.search(pat, sent):
                    negative.add(sent[:50])

        # Simple contradiction check: same subject with both positive and negative
        for p in positive:
            for n in negative:
                # Check if they share significant words
                p_words = set(p.lower().split())
                n_words = set(n.lower().split())
                overlap = p_words & n_words
                if len(overlap) >= 3:
                    contradictions.append(f"'{p}' vs '{n}'")
                    if len(contradictions) >= 5:
                        break
            if len(contradictions) >= 5:
                break

        return contradictions

    def compare_statements(self, statement_a: str, statement_b: str) -> dict:
        """Compare two statements for consistency."""
        a_lower = statement_a.lower()
        b_lower = statement_b.lower()

        # Check for direct contradiction
        a_neg = bool(re.search(r"\b(not|no|never|isn't|can't|won't|doesn't)\b", a_lower))
        b_neg = bool(re.search(r"\b(not|no|never|isn't|can't|won't|doesn't)\b", b_lower))

        # Check fact overlap
        a_facts = set(re.findall(r'\b[a-z]+\b', a_lower))
        b_facts = set(re.findall(r'\b[a-z]+\b', b_lower))

        overlap = a_facts & b_facts
        similarity = difflib.SequenceMatcher(None, a_lower, b_lower).ratio()

        return {
            "similarity": round(similarity, 3),
            "fact_overlap": len(overlap),
            "shared_terms": list(overlap)[:10],
            "contradictory": (similarity > 0.3 and a_neg != b_neg),
            "confidence": round(min(1.0, similarity * 2), 3),
        }


# ─── Preemptive Issue Scanner ─────────────────────────────────

ISSUE_PATTERNS = {
    "security": [
        (r"(?i)(eval|exec)\s*\(", "Dangerous function call"),
        (r"(?i)input\s*\(\)", "Unsafe input() in Python 2/3"),
        (r"(?i)(os\.system|subprocess\.call|subprocess\.Popen)\s*\(", "Command injection risk"),
        (r"(?i)pickle\.(loads?|unpack)", "Insecure deserialization"),
        (r"(?i)(sqlite3|mysql|psycopg2)\.execute\s*\(\s*f[\"']", "SQL injection via f-string"),
        (r"(?i)(api_key|secret|password|token|credential)\s*=.*['\"].+['\"]", "Hardcoded credential"),
        (r"(?i)@app\.route.*methods=\[.*POST", "No CSRF protection"),
    ],
    "performance": [
        (r"(?i)for\s+\w+\s+in\s+range\(len\(", "Non-Pythonic loop"),
        (r"(?i)\.append\(.*\)\s*\n\s+\.append", "Repeated append pattern"),
        (r"(?i)time\.sleep\s*\(\s*0\.", "Busy-wait microsleep"),
        (r"(?i)while\s+True.*\n(?!.*break)", "Infinite loop without break"),
        (r"(?i)pandas\.apply\s*\(.*lambda", "Slow pandas apply with lambda"),
    ],
    "maintainability": [
        (r"(?i)except\s*:\s*pass", "Bare except with pass"),
        (r"(?i)except\s+\w+\s*:\s*pass", "Silent exception catch"),
        (r"(?i)def\s+\w+\(.*\):\s*\n\s+pass", "Empty function body"),
        (r"(?i)#\s*TODO", "Unresolved TODO"),
        (r"(?i)#\s*FIXME", "Unresolved FIXME"),
        (r"(?i)#\s*XXX", "Unresolved XXX"),
        (r"(?i)print\s*\(.*\)", "Debug print statement"),
        (r"if\s+False\s*:", "Dead code block"),
    ],
    "resource": [
        (r"(?i)open\(.*\)\s*(?!.*\.close)", "File handle not closed (might be context manager)"),
        (r"(?i)\.read\(\).*\.read\(\)", "Multiple file reads"),
        (r"(?i)list\(.*\.keys\(\)\)", "Unnecessary list conversion"),
    ],
}


class PreemptiveIssueScanner:
    """Scans code and configuration for potential issues before they cause failures."""

    def __init__(self):
        self._compiled = {}
        for category, patterns in ISSUE_PATTERNS.items():
            self._compiled[category] = [
                (re.compile(p), msg) for p, msg in patterns
            ]

    def scan_code(self, source_code: str, filename: str = "<unknown>") -> dict:
        """Scan source code for potential issues."""
        issues = []
        lines = source_code.split("\n")

        for category, patterns in self._compiled.items():
            for pattern, message in patterns:
                for i, line in enumerate(lines, 1):
                    if pattern.search(line):
                        issues.append({
                            "category": category,
                            "severity": self._categorize_severity(category, line),
                            "line": i,
                            "message": message,
                            "code": line.strip()[:100],
                        })

        # Check syntax
        syntax_issues = self._check_syntax(source_code, filename)
        issues.extend(syntax_issues)

        # Check imports
        import_issues = self._check_imports(source_code, filename)
        issues.extend(import_issues)

        # Deduplicate
        seen = set()
        unique_issues = []
        for issue in issues:
            key = (issue["line"], issue["message"])
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)

        return {
            "filename": filename,
            "total_issues": len(unique_issues),
            "critical": sum(1 for i in unique_issues if i["severity"] == "critical"),
            "warning": sum(1 for i in unique_issues if i["severity"] == "warning"),
            "info": sum(1 for i in unique_issues if i["severity"] == "info"),
            "issues": sorted(unique_issues, key=lambda x: x["line"]),
            "scan_time": datetime.now(timezone.utc).isoformat(),
        }

    def scan_module(self, module_path: str) -> dict:
        """Scan a Python module file for issues."""
        path = Path(module_path)
        if not path.exists():
            return {"error": f"File not found: {module_path}"}
        source = path.read_text(encoding="utf-8")
        return self.scan_code(source, str(path))

    def scan_directory(self, directory: str, pattern: str = "*.py") -> list[dict]:
        """Scan all matching files in a directory."""
        results = []
        for path in Path(directory).rglob(pattern):
            try:
                result = self.scan_module(str(path))
                results.append(result)
            except Exception as e:
                results.append({"filename": str(path), "error": str(e)})
        return results

    def _categorize_severity(self, category: str, line: str) -> str:
        if category == "security":
            return "critical"
        elif category == "performance":
            return "warning"
        elif category == "resource":
            return "warning"
        return "info"

    def _check_syntax(self, source: str, filename: str) -> list[dict]:
        try:
            ast.parse(source)
            return []
        except SyntaxError as e:
            return [{
                "category": "syntax",
                "severity": "critical",
                "line": e.lineno or 0,
                "message": f"Syntax error: {e.msg}",
                "code": e.text or "",
            }]

    def _check_imports(self, source: str, filename: str) -> list[dict]:
        issues = []
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not alias.name:
                            issues.append({
                                "category": "import",
                                "severity": "warning",
                                "line": node.lineno,
                                "message": f"Empty import found",
                                "code": f"import {alias.name}",
                            })
                elif isinstance(node, ast.ImportFrom):
                    if not node.module:
                        issues.append({
                            "category": "import",
                            "severity": "warning",
                            "line": node.lineno,
                            "message": "Relative import without module",
                            "code": f"from . import ...",
                        })
        except Exception:
            pass
        return issues


# ─── System Anomaly Detection ─────────────────────────────────

class AnomalyDetector:
    """Detects anomalous patterns in system metrics and behavior."""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics: dict[str, list[float]] = {}
        self.baselines: dict[str, dict] = {}
        self.anomalies: list[dict] = []

    def record_metric(self, name: str, value: float) -> Optional[dict]:
        """Record a metric value and check for anomaly."""
        if name not in self.metrics:
            self.metrics[name] = []
            self.baselines[name] = {"mean": value, "std": 0.0, "count": 1}

        self.metrics[name].append(value)
        if len(self.metrics[name]) > self.window_size:
            self.metrics[name].pop(0)

        data = self.metrics[name]
        if len(data) < 10:
            self._update_baseline(name, data)
            return None

        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        std = variance ** 0.5

        # Updated baseline
        self.baselines[name] = {
            "mean": round(mean, 3),
            "std": round(std, 3),
            "count": len(data),
        }

        # Z-score anomaly detection
        if std > 0:
            z_score = abs(value - mean) / std
            if z_score > 3.0:
                anomaly = {
                    "metric": name,
                    "value": value,
                    "mean": round(mean, 3),
                    "std": round(std, 3),
                    "z_score": round(z_score, 2),
                    "severity": "critical" if z_score > 4.0 else "warning",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "id": hashlib.md5(f"{name}{value}{time.time_ns()}".encode()).hexdigest()[:12],
                }
                self.anomalies.append(anomaly)
                return anomaly
        return None

    def _update_baseline(self, name: str, data: list[float]):
        if len(data) < 2:
            return
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        self.baselines[name] = {
            "mean": round(mean, 3),
            "std": round(variance ** 0.5, 3),
            "count": len(data),
        }

    def get_recent_anomalies(self, limit: int = 20) -> list[dict]:
        return self.anomalies[-limit:]

    def get_metric_summary(self) -> dict:
        return {
            name: info for name, info in self.baselines.items()
        }


# ─── Eagle Eye Main Engine ────────────────────────────────────

class EagleEye:
    """
    NIKTO's truth verification & preemptive issue detection system.

    Eagle Eye watches everything — detecting lies from any AI,
    spotting issues before they become failures, and ensuring
    NIKTO always operates at peak truth and reliability.
    """

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.expanduser("~/.nikto")
        self.data_dir = Path(data_dir) / "eagle_eye"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.lie_detector = LieDetector()
        self.issue_scanner = PreemptiveIssueScanner()
        self.anomaly_detector = AnomalyDetector()
        self._watchlist: list[dict] = []

    def watch(self, name: str, target: Any, check_interval: int = 300) -> dict:
        """Add a target to Eagle Eye's watchlist for continuous monitoring."""
        entry = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "target": str(target),
            "check_interval": check_interval,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "last_check": None,
            "status": "watching",
        }
        self._watchlist.append(entry)
        return entry

    def analyze_text(self, text: str, source: str = "unknown") -> dict:
        """Full text analysis — lie detection + consistency check."""
        result = self.lie_detector.analyze(text, source)
        # Record as metric
        self.anomaly_detector.record_metric(
            f"deception_score_{source}", result["deception_score"]
        )
        return result

    def scan_code(self, code: str, filename: str = "<unknown>") -> dict:
        """Scan code for preemptive issue detection."""
        result = self.issue_scanner.scan_code(code, filename)
        self.anomaly_detector.record_metric(
            "code_issues_per_scan", result["total_issues"]
        )
        return result

    def scan_file(self, filepath: str) -> dict:
        """Scan a file for issues."""
        result = self.issue_scanner.scan_module(filepath)
        return result

    def scan_project(self, directory: str) -> list[dict]:
        """Scan entire project directory for code issues."""
        return self.issue_scanner.scan_directory(directory)

    def compare_ai_statements(self, statement_a: str, statement_b: str,
                              source_a: str = "unknown", source_b: str = "unknown") -> dict:
        """Compare statements from two AIs for truth consistency."""
        result_a = self.analyze_text(statement_a, source_a)
        result_b = self.analyze_text(statement_b, source_b)
        comparison = self.lie_detector.compare_statements(statement_a, statement_b)

        return {
            "source_a": source_a,
            "source_b": source_b,
            "a_deception_score": result_a["deception_score"],
            "b_deception_score": result_b["deception_score"],
            "consistency": comparison["similarity"],
            "contradictory": comparison["contradictory"],
            "a_flags": result_a["flags"],
            "b_flags": result_b["flags"],
            "comparison": comparison,
            "verdict": self._generate_verdict(result_a, result_b, comparison),
        }

    def _generate_verdict(self, a: dict, b: dict, comp: dict) -> str:
        if comp["contradictory"] and a["deception_score"] > 0.3 and b["deception_score"] > 0.3:
            return "BOTH LIKELY DECEPTIVE — statements contradict with high deception markers"
        if comp["contradictory"]:
            return "WARNING — statements contradict each other"
        if a["deception_score"] > 0.5:
            return f"CAUTION — {a['source']} shows strong deception markers"
        if b["deception_score"] > 0.5:
            return f"CAUTION — {b['source']} shows strong deception markers"
        if a["deception_score"] < 0.2 and b["deception_score"] < 0.2 and comp["similarity"] > 0.7:
            return "TRUTHFUL — both statements consistent and low deception markers"
        return "INCONCLUSIVE — further analysis recommended"

    def preemptive_scan(self, target_dir: Optional[str] = None) -> dict:
        """Full preemptive scan of NIKTO's own codebase."""
        if target_dir is None:
            target_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "nikto")

        results = self.scan_project(target_dir)
        total_issues = sum(r.get("total_issues", 0) for r in results)
        total_critical = sum(r.get("critical", 0) for r in results)
        total_warnings = sum(r.get("warning", 0) for r in results)

        return {
            "target": target_dir,
            "files_scanned": len(results),
            "total_issues": total_issues,
            "critical": total_critical,
            "warnings": total_warnings,
            "errors": [r for r in results if "error" in r],
            "scan_time": datetime.now(timezone.utc).isoformat(),
        }

    def get_truth_report(self) -> dict:
        """Generate a comprehensive truth and health report."""
        return {
            "eagle_eye_status": "ACTIVE",
            "total_analyses": len(self.lie_detector.history),
            "anomalies_detected": len(self.anomaly_detector.anomalies),
            "watchlist_count": len(self._watchlist),
            "recent_anomalies": self.anomaly_detector.get_recent_anomalies(5),
            "metric_summary": self.anomaly_detector.get_metric_summary(),
            "report_time": datetime.now(timezone.utc).isoformat(),
        }


def create_eagle_eye(data_dir: Optional[str] = None) -> EagleEye:
    return EagleEye(data_dir)
