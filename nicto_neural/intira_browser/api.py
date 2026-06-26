"""Intira API — Programmatic interface between NICTO and Intira Browser."""
import asyncio
import json
import logging
from typing import Optional, List, Dict, Any


logger = logging.getLogger(__name__)


class IntiraAPI:
    """High-level API for NICTO to control the Intira Browser.

    Provides convenience methods for common browsing patterns:
    search, fetch, extract, screenshot, and autonomous tasks.
    All backed by a real Chromium browser instance.
    """

    def __init__(self, headless: bool = True):
        self._browser = None
        self._search = None
        self._agent = None
        self._headless = headless
        self._initialized = False

    async def _ensure(self):
        """Lazy-init browser and subsystems."""
        if self._initialized:
            return
        from .browser import IntiraBrowser
        from .search import IntiraSearch
        from .agent import IntiraAgent

        self._browser = IntiraBrowser(headless=self._headless)
        await self._browser.launch()
        self._search = IntiraSearch(browser=self._browser)
        self._agent = IntiraAgent(browser=self._browser)
        self._initialized = True
        logger.info("Intira API ready")

    async def search(self, query: str, count: int = 10, engine: str = "duckduckgo") -> dict:
        """Search the web. Returns structured results + summary."""
        await self._ensure()
        results = await self._search.search(query, count=count, engine=engine, extract_content=False)
        return {
            "query": query,
            "engine": engine,
            "count": len(results),
            "results": [
                {"title": r.title, "url": r.url, "snippet": r.snippet, "position": r.position}
                for r in results
            ],
        }

    async def search_and_summarize(self, query: str, count: int = 5, engine: str = "duckduckgo") -> str:
        """Search and return a consolidated text summary."""
        await self._ensure()
        from .extractor import ContentExtractor
        extractor = ContentExtractor()

        results = await self._search.search(query, count=count, engine=engine, extract_content=True)
        if not results:
            return f"No results found for: {query}"

        extracted = []
        for r in results:
            html = r.content or r.snippet
            if html:
                ex = extractor.extract(r.url, r.title, f"<html><body>{html}</body></html>", r.content)
                extracted.append(ex)

        if extracted:
            return extractor.create_summary(extracted)
        return " ".join(r.snippet for r in results if r.snippet)[:500]

    async def fetch(self, url: str) -> dict:
        """Fetch and extract content from a URL."""
        await self._ensure()
        content = await self._search.fetch_page(url)
        text = content[:3000] if content else ""
        return {
            "url": url,
            "content_length": len(content),
            "content": text,
        }

    async def navigate(self, url: str) -> dict:
        """Navigate browser to URL."""
        await self._ensure()
        return await self._agent.navigate(url)

    async def extract_current_page(self) -> dict:
        """Extract structured content from current page."""
        await self._ensure()
        return await self._agent.extract_page()

    async def screenshot(self) -> Optional[str]:
        """Take a screenshot of current page."""
        await self._ensure()
        return await self._agent.screenshot()

    async def run_task(self, task: str, steps: List[dict]) -> dict:
        """Run an autonomous multi-step browsing task."""
        await self._ensure()
        return await self._agent.run_task(task, steps)

    async def get_browser_status(self) -> dict:
        """Get Intira Browser status."""
        if self._browser:
            return self._browser.get_status()
        return {"running": False}

    async def get_history(self) -> List[dict]:
        """Get agent action history."""
        if self._agent:
            return self._agent.get_history()
        return []

    async def close(self):
        """Shut down Intira Browser and all subsystems."""
        if self._agent:
            await self._agent.close()
        if self._search:
            await self._search.close()
        if self._browser:
            await self._browser.shutdown()
        self._initialized = False
        logger.info("Intira API shut down")
