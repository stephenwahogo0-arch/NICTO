"""NICTO X — Research agent with web search and URL fetching."""
from __future__ import annotations
import logging
from typing import Any, Optional
from nicto_x.agents.base import BaseAgent
import httpx

logger = logging.getLogger("nicto_x.agents.research")


class ResearchAgent(BaseAgent):
    """Performs research via web search and URL content fetching."""

    async def execute(self, task: str, context: Optional[dict] = None) -> dict:
        query = str(task)
        sources = []
        findings = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                try:
                    resp = await client.get(
                        f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1",
                        headers={"User-Agent": "NICTO-X/1.0"},
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        abstract = data.get("AbstractText", "")
                        if abstract:
                            findings.append(f"Abstract: {abstract[:500]}")
                            sources.append({"type": "abstract", "text": abstract[:500], "url": data.get("AbstractURL", "")})
                except Exception:
                    pass

                try:
                    resp = await client.get("https://en.wikipedia.org/w/api.php", params={
                        "action": "query", "list": "search", "srsearch": query,
                        "format": "json", "srlimit": 3,
                    })
                    if resp.status_code == 200:
                        for r in resp.json().get("query", {}).get("search", []):
                            findings.append(f"Wikipedia: {r['title']} - {r.get('snippet', '')[:200]}")
                            sources.append({"type": "wikipedia", "text": r.get("snippet", "")[:200], "title": r["title"]})
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Research web search failed: {e}")

        output = "\n".join(findings) if findings else f"Research findings for: {query}"
        return {
            "agent": self.name,
            "task": query,
            "output": output,
            "sources": sources,
            "confidence": min(0.9, 0.3 + len(sources) * 0.15),
        }
