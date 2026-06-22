"""
Language Detection Module for NIKTO.

Detects the language of text using langdetect (if available) or
Unicode heuristics as a fallback.
"""

from typing import Optional

SUPPORTED_LANGUAGES: list[str] = [
    "af", "sq", "ar", "hy", "az", "eu", "be", "bn", "bs", "bg",
    "ca", "ceb", "zh", "zh-cn", "zh-tw", "co", "hr", "cs", "da", "nl",
    "en", "eo", "et", "fi", "fr", "fy", "gl", "ka", "de", "el",
    "gu", "ht", "ha", "haw", "he", "hi", "hmn", "hu", "is", "ig",
    "id", "ga", "it", "ja", "jv", "kn", "kk", "km", "rw", "ko",
    "ku", "ky", "lo", "la", "lv", "lt", "lb", "mk", "mg", "ms",
    "ml", "mt", "mi", "mr", "mn", "my", "ne", "no", "ny", "or",
    "ps", "fa", "pl", "pt", "pa", "ro", "ru", "sm", "gd", "sr",
    "st", "sn", "sd", "si", "sk", "sl", "so", "es", "su", "sw",
    "sv", "tl", "tg", "ta", "tt", "te", "th", "tr", "tk", "uk",
    "ur", "ug", "uz", "vi", "cy", "xh", "yi", "yo", "zu",
]


class LanguageDetector:
    """Detects the language of input text."""

    def __init__(self) -> None:
        self._langdetect_available = False
        self._init_backend()

    def _init_backend(self) -> None:
        try:
            import langdetect  # type: ignore[import-untyped]
            self._langdetect = langdetect
            self._langdetect_available = True
        except ImportError:
            self._langdetect_available = False

    def detect(self, text: str) -> str:
        """Detect the ISO language code of *text*.

        Returns ``"en"`` when detection is not possible.
        """
        if not text or not text.strip():
            return "en"
        if self._langdetect_available:
            try:
                return self._langdetect.detect(text)
            except Exception:
                pass
        return self._heuristic_detect(text)

    def detect_confidence(self, text: str) -> tuple[str, float]:
        """Return ``(language_code, confidence)``."""
        if not text or not text.strip():
            return ("en", 0.0)
        if self._langdetect_available:
            try:
                langs = self._langdetect.detect_langs(text)
                if langs:
                    best = langs[0]
                    return (best.lang, best.prob)
            except Exception:
                pass
        code = self._heuristic_detect(text)
        return (code, 0.5)

    # ------------------------------------------------------------------
    # Unicode-range fallback
    # ------------------------------------------------------------------
    _HEURISTIC_RANGES: list[tuple[str, tuple[int, int], float]] = [
        # (code, (start, end), threshold_ratio)
        ("zh", (0x4E00, 0x9FFF), 0.05),
        ("zh", (0x3400, 0x4DBF), 0.05),
        ("ja", (0x3040, 0x309F), 0.02),
        ("ja", (0x30A0, 0x30FF), 0.02),
        ("ko", (0xAC00, 0xD7AF), 0.05),
        ("ru", (0x0400, 0x04FF), 0.05),
        ("ar", (0x0600, 0x06FF), 0.05),
        ("he", (0x0590, 0x05FF), 0.05),
        ("th", (0x0E00, 0x0E7F), 0.05),
        ("hi", (0x0900, 0x097F), 0.05),
        ("el", (0x0370, 0x03FF), 0.05),
    ]

    def _heuristic_detect(self, text: str) -> str:
        total = max(len(text), 1)
        for code, (lo, hi), threshold in self._HEURISTIC_RANGES:
            count = sum(1 for c in text if lo <= ord(c) <= hi)
            if count / total > threshold:
                return code
        return "en"

    def get_supported_languages(self) -> list[str]:
        """Return the full list of supported ISO language codes."""
        return list(SUPPORTED_LANGUAGES)
