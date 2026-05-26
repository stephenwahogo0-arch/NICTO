import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EliminationResult:
    is_clean: bool
    issues: list = field(default_factory=list)
    safe_response: Optional[str] = None


FALSE_PATTERNS = [
    (re.compile(r"\b\d+%\s+of\s+(scientists?|experts?|doctors?|researchers?)\s+agree\b", re.IGNORECASE),
     "Misleading statistics: X% of Y agree"),
    (re.compile(r"\b(vaccine|cure).*\b(cancer|autism)\b.*\b(cause|causes|caused)\b", re.IGNORECASE),
     "Medical misinformation: vaccine/cure disclaimer needed"),
    (re.compile(r"\b(great wall|wall of china).*\b(visible|see).*\b(space|moon)\b", re.IGNORECASE),
     "Common myth: Great Wall visible from space"),
    (re.compile(r"\b(humans?|we|people).*\b(only|just).*\b\d+\s*%\s+of\s+(their\s+|the\s+)?(brain|mind)\b", re.IGNORECASE),
     "Common myth: 10% brain usage"),
    (re.compile(r"\b(einstein|albert einstein).*\bfailed.*\b(math|mathematics)\b", re.IGNORECASE),
     "Common myth: Einstein failed math"),
    (re.compile(r"\b(moon landing|apollo).*\b(fake|hoax|staged|studio)\b", re.IGNORECASE),
     "Conspiracy theory: moon landing hoax"),
    (re.compile(r"\b(guaranteed|risk.free|no.risk).*\b(return|profit|income)\b", re.IGNORECASE),
     "Financial misinformation: guaranteed returns"),
    (re.compile(r"\b(chemtrails|flat earth|illuminati|new world order)\b", re.IGNORECASE),
     "Conspiracy theory reference"),
    (re.compile(r"\b(cancer|cure).*\b(overnight|miracle|secret)\b", re.IGNORECASE),
     "Miracle cure claim"),
    (re.compile(r"\b(1\d{3}|2\d{3})\s*(B.C.|A.D.|BC|AD|CE|BCE)\b.*\b(invented|discovered)\b.*\b(computer|phone|internet)\b", re.IGNORECASE),
     "Anachronism: technology out of time period"),
]


class HallucinationEliminator:
    def __init__(self):
        self.patterns = FALSE_PATTERNS
        self._stats = {"total_checks": 0, "flags_raised": 0}

    def check_response(self, text: str) -> EliminationResult:
        self._stats["total_checks"] += 1
        issues = []
        for pattern, description in self.patterns:
            matches = pattern.findall(text)
            if matches:
                issues.append({"pattern": description, "matches": len(matches), "severity": "high"})
        is_clean = len(issues) == 0
        if is_clean:
            return EliminationResult(is_clean=True, issues=[], safe_response=text)
        self._stats["flags_raised"] += 1
        safe_response = self._sanitize(text, issues)
        return EliminationResult(is_clean=False, issues=issues, safe_response=safe_response)

    def _sanitize(self, text: str, issues: list) -> str:
        safe = text
        for issue in issues:
            disclaimer = f"\n\n[DISCLAIMER: {issue['pattern']} detected. Please verify this claim with reliable sources.]"
            safe += disclaimer
        return safe

    def get_stats(self) -> dict:
        return dict(self._stats)
