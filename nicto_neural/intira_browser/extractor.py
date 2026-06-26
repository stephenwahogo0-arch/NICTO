"""Content extraction engine for Intira Browser."""
import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


logger = logging.getLogger(__name__)


STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "it", "its", "this", "that", "these", "those", "i", "you", "he", "she",
    "we", "they", "me", "him", "her", "us", "them", "not", "no", "nor", "so",
    "if", "then", "than", "too", "very", "just", "about", "also", "more",
    "some", "any", "each", "every", "all", "both", "few", "most", "other",
    "into", "over", "such", "only", "own", "same", "how", "what", "which",
    "who", "whom", "when", "where", "why",
}


@dataclass
class ExtractedPage:
    url: str
    title: str
    text: str
    summary: str = ""
    keywords: List[str] = field(default_factory=list)
    sentences: List[str] = field(default_factory=list)
    word_count: int = 0
    reading_time_seconds: int = 0
    language: str = "en"
    headings: List[Dict[str, str]] = field(default_factory=list)
    links: List[Dict[str, str]] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)


class ContentExtractor:
    """Extract, process, and structure web content for NICTO."""

    def __init__(self, max_summary_sentences: int = 5):
        self.max_summary_sentences = max_summary_sentences

    def extract(self, url: str, title: str, html: str, text: str = "") -> ExtractedPage:
        """Extract structured content from a web page."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml") if html else None

        content_text = text or (soup.get_text(separator=" ", strip=True) if soup else "")
        content_text = re.sub(r'\s+', ' ', content_text).strip()

        sentences = self._split_sentences(content_text)
        summary = " ".join(sentences[:self.max_summary_sentences])
        keywords = self._extract_keywords(content_text)
        word_count = len(content_text.split())
        reading_time = int(word_count / 200 * 60)

        headings = []
        if soup:
            for tag in ["h1", "h2", "h3"]:
                for h in soup.select(tag):
                    headings.append({"level": tag, "text": h.get_text(strip=True)})

        links = []
        if soup:
            for a in soup.select("a[href]")[:50]:
                href = a.get("href", "")
                if href.startswith("http"):
                    links.append({"text": a.get_text(strip=True)[:80], "href": href})

        images = []
        if soup:
            for img in soup.select("img[src]")[:20]:
                src = img.get("src", "")
                if src.startswith(("http://", "https://", "//")):
                    if src.startswith("//"):
                        src = "https:" + src
                    images.append(src)

        return ExtractedPage(
            url=url,
            title=title,
            text=content_text,
            summary=summary,
            keywords=keywords[:20],
            sentences=sentences,
            word_count=word_count,
            reading_time_seconds=reading_time,
            headings=headings,
            links=links,
            images=images,
        )

    def _split_sentences(self, text: str) -> List[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 15]

    def _extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r'[a-zA-Z]{3,}', text.lower())
        freq = {}
        for w in words:
            if w not in STOP_WORDS:
                freq[w] = freq.get(w, 0) + 1
        return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:50]]

    def create_summary(self, extracted: List[ExtractedPage], max_sentences: int = 10) -> str:
        """Create a consolidated summary across multiple extracted pages."""
        all_sentences = []
        for ex in extracted:
            all_sentences.extend(ex.sentences)

        seen = set()
        unique = []
        for s in all_sentences:
            key = s.lower().strip()[:60]
            if key not in seen:
                seen.add(key)
                unique.append(s)

        return " ".join(unique[:max_sentences])
