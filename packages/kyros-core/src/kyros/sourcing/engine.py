"""Sourcing Engine — tracks, manages, and formats citations and sources."""
import json
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class Citation:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    url: str = ""
    title: str = ""
    author: str = ""
    date_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    date_published: Optional[str] = None
    content_snippet: str = ""
    relevance_score: float = 1.0
    source_type: str = "web"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        if self.author and self.date_published:
            return f"[{self.title}]({self.url}) — {self.author}, {self.date_published}"
        elif self.author:
            return f"[{self.title}]({self.url}) — {self.author}"
        else:
            return f"[{self.title}]({self.url})"

    def to_footnote(self) -> str:
        parts = []
        if self.author:
            parts.append(self.author)
        if self.date_published:
            parts.append(f"({self.date_published})")
        parts.append(f"*{self.title}*")
        if self.url:
            parts.append(f"Retrieved from {self.url}")
        return ". ".join(parts)


@dataclass
class SourcedClaim:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    claim: str = ""
    citations: List[Citation] = field(default_factory=list)
    confidence: float = 0.8
    claim_type: str = "factual"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_citation(self, citation: Citation) -> None:
        self.citations.append(citation)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "claim": self.claim,
            "citations": [c.to_dict() for c in self.citations],
            "confidence": self.confidence,
            "claim_type": self.claim_type,
            "created_at": self.created_at,
        }

    def to_markdown_with_citations(self) -> str:
        if not self.citations:
            return self.claim
        citation_refs = " ".join([f"[{i+1}]" for i in range(len(self.citations))])
        return f"{self.claim} {citation_refs}"


class SourcingEngine:
    def __init__(self, data_dir: str = ""):
        from pathlib import Path
        self.data_dir = Path(data_dir) / "sourcing" if data_dir else Path.home() / ".nikto" / "sourcing"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.citations_file = self.data_dir / "citations.jsonl"
        self.claims_file = self.data_dir / "sourced_claims.jsonl"
        self.current_session_citations: Dict[str, Citation] = {}
        self.current_session_claims: List[SourcedClaim] = []

    def add_web_source(self, url: str, title: str, content_snippet: str = "",
                       author: str = "", date_published: Optional[str] = None,
                       relevance_score: float = 1.0) -> Citation:
        citation = Citation(url=url, title=title, author=author,
                           date_published=date_published, content_snippet=content_snippet,
                           relevance_score=relevance_score, source_type="web")
        self.current_session_citations[citation.id] = citation
        self._save_citation(citation)
        return citation

    def add_knowledge_base_source(self, title: str, content_snippet: str = "",
                                   relevance_score: float = 0.9) -> Citation:
        citation = Citation(url="internal://knowledge_base", title=title,
                           content_snippet=content_snippet, relevance_score=relevance_score,
                           source_type="knowledge_base")
        self.current_session_citations[citation.id] = citation
        self._save_citation(citation)
        return citation

    def add_academic_source(self, title: str, author: str, date_published: str,
                            url: str = "", content_snippet: str = "",
                            relevance_score: float = 0.95) -> Citation:
        citation = Citation(url=url, title=title, author=author,
                           date_published=date_published, content_snippet=content_snippet,
                           relevance_score=relevance_score, source_type="academic")
        self.current_session_citations[citation.id] = citation
        self._save_citation(citation)
        return citation

    def create_sourced_claim(self, claim: str, citations: List[Citation],
                              confidence: float = 0.8, claim_type: str = "factual") -> SourcedClaim:
        sourced_claim = SourcedClaim(claim=claim, citations=citations,
                                     confidence=confidence, claim_type=claim_type)
        self.current_session_claims.append(sourced_claim)
        self._save_claim(sourced_claim)
        return sourced_claim

    def format_response_with_sources(self, response_text: str, claims: List[SourcedClaim]) -> str:
        if not claims:
            return response_text
        citations_section = "\n\n---\n\n## Sources\n\n"
        unique_citations = {}
        for claim in claims:
            for citation in claim.citations:
                if citation.id not in unique_citations:
                    unique_citations[citation.id] = citation
        for i, (cid, citation) in enumerate(unique_citations.items(), 1):
            citations_section += f"{i}. {citation.to_markdown()}\n"
            if citation.content_snippet:
                citations_section += f"   > {citation.content_snippet[:150]}...\n"
            citations_section += "\n"
        return response_text + citations_section

    def get_session_summary(self) -> Dict[str, Any]:
        return {
            "total_citations": len(self.current_session_citations),
            "total_claims": len(self.current_session_claims),
            "citations_by_type": self._count_by_type(),
            "average_confidence": self._average_confidence(),
            "citations": [c.to_dict() for c in self.current_session_citations.values()],
            "claims": [c.to_dict() for c in self.current_session_claims],
        }

    def _count_by_type(self) -> Dict[str, int]:
        counts = {}
        for c in self.current_session_citations.values():
            counts[c.source_type] = counts.get(c.source_type, 0) + 1
        return counts

    def _average_confidence(self) -> float:
        if not self.current_session_claims:
            return 0.0
        return sum(c.confidence for c in self.current_session_claims) / len(self.current_session_claims)

    def _save_citation(self, citation: Citation) -> None:
        try:
            with open(self.citations_file, "a") as f:
                f.write(json.dumps(citation.to_dict()) + "\n")
        except Exception:
            pass

    def _save_claim(self, claim: SourcedClaim) -> None:
        try:
            with open(self.claims_file, "a") as f:
                f.write(json.dumps(claim.to_dict()) + "\n")
        except Exception:
            pass

    def clear_session(self) -> None:
        self.current_session_citations.clear()
        self.current_session_claims.clear()
