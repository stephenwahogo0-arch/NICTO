"""Intira Agent — autonomous web interaction agent for NICTO."""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable


logger = logging.getLogger(__name__)


@dataclass
class IntiraAction:
    """An action the agent can perform in the browser."""
    type: str
    params: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = False
    timestamp: float = 0.0


@dataclass
class AgentStep:
    """A single step in an autonomous browsing session."""
    action: IntiraAction
    observation: str = ""
    thought: str = ""
    completed: bool = False
    error: Optional[str] = None


class IntiraAgent:
    """Autonomous web interaction agent.

    IntiraAgent can browse the web autonomously — searching, navigating,
    filling forms, extracting data, and reporting back to the NICTO brain.
    """

    def __init__(self, browser=None, max_steps: int = 20):
        self._browser = browser
        self._max_steps = max_steps
        self._history: List[AgentStep] = []
        self._current_task: str = ""

    async def ensure_browser(self):
        if self._browser is None:
            from .browser import IntiraBrowser
            self._browser = IntiraBrowser(headless=True)
            await self._browser.launch()

    async def search(self, query: str, engine: str = "duckduckgo", count: int = 10) -> List[dict]:
        """Search the web and return structured results."""
        await self.ensure_browser()
        from .search import IntiraSearch
        searcher = IntiraSearch(browser=self._browser)
        results = await searcher.search(query, count=count, engine=engine, extract_content=False)

        step = AgentStep(
            action=IntiraAction(type="search", params={"query": query, "engine": engine}, timestamp=time.time()),
            observation=f"Found {len(results)} results for '{query}'",
            completed=True,
        )
        self._history.append(step)

        return [
            {"title": r.title, "url": r.url, "snippet": r.snippet, "source": r.source}
            for r in results
        ]

    async def navigate(self, url: str) -> dict:
        """Navigate to a specific URL."""
        await self.ensure_browser()
        title = await self._browser.navigate(url)
        page_url = await self._browser.get_page_url()

        step = AgentStep(
            action=IntiraAction(type="navigate", params={"url": url}, timestamp=time.time()),
            observation=f"Navigated to '{title}' at {page_url}",
            completed=True,
        )
        self._history.append(step)

        return {"url": page_url, "title": title}

    async def extract_page(self) -> dict:
        """Extract all content from the current page."""
        await self.ensure_browser()
        from .extractor import ContentExtractor
        extractor = ContentExtractor()

        url = await self._browser.get_page_url()
        title = await self._browser.get_page_title()
        html = await self._browser.get_page_html()
        text = await self._browser.get_page_text()

        extracted = extractor.extract(url, title, html, text)

        step = AgentStep(
            action=IntiraAction(type="extract", params={}, timestamp=time.time()),
            observation=f"Extracted {extracted.word_count} words, {len(extracted.links)} links, {len(extracted.images)} images",
            completed=True,
        )
        self._history.append(step)

        return {
            "url": extracted.url,
            "title": extracted.title,
            "summary": extracted.summary,
            "keywords": extracted.keywords[:15],
            "word_count": extracted.word_count,
            "reading_time_seconds": extracted.reading_time_seconds,
            "headings": extracted.headings[:10],
            "links": extracted.links[:20],
            "images": extracted.images[:10],
        }

    async def click(self, selector: str, wait_ms: int = 1000) -> bool:
        """Click an element on the page."""
        await self.ensure_browser()
        success = await self._browser.click(selector)
        if success:
            await self._browser.wait_for_timeout(wait_ms)

        step = AgentStep(
            action=IntiraAction(type="click", params={"selector": selector}, timestamp=time.time()),
            observation=f"Click on '{selector}': {'success' if success else 'failed'}",
            completed=success,
            error=None if success else f"Element '{selector}' not clickable",
        )
        self._history.append(step)
        return success

    async def fill(self, selector: str, value: str) -> bool:
        """Fill a form field."""
        await self.ensure_browser()
        success = await self._browser.fill_input(selector, value)

        step = AgentStep(
            action=IntiraAction(type="fill", params={"selector": selector}, timestamp=time.time()),
            observation=f"Fill '{selector}' = '{value[:50]}': {'success' if success else 'failed'}",
            completed=success,
        )
        self._history.append(step)
        return success

    async def screenshot(self) -> Optional[str]:
        """Take a screenshot."""
        await self.ensure_browser()
        return await self._browser.screenshot()

    async def get_links(self) -> List[dict]:
        """Get all links on the current page."""
        await self.ensure_browser()
        return await self._browser.get_links()

    async def run_task(self, task_description: str, steps: Optional[List[dict]] = None) -> dict:
        """Run an autonomous browsing task based on a series of actions.

        Args:
            task_description: Human-readable description of the task.
            steps: List of action dicts, e.g.:
                [{"type": "search", "query": "..."},
                 {"type": "click", "selector": "..."},
                 {"type": "extract"}]
        """
        self._current_task = task_description
        self._history = []
        await self.ensure_browser()

        if not steps:
            return {
                "task": task_description,
                "success": False,
                "error": "No steps provided",
                "steps_completed": 0,
            }

        for i, step_def in enumerate(steps[:self._max_steps]):
            action_type = step_def.get("type")
            params = {k: v for k, v in step_def.items() if k != "type"}

            try:
                if action_type == "search":
                    result = await self.search(**params)
                elif action_type == "navigate":
                    result = await self.navigate(**params)
                elif action_type == "extract":
                    result = await self.extract_page()
                elif action_type == "click":
                    result = await self.click(**params)
                elif action_type == "fill":
                    result = await self.fill(**params)
                elif action_type == "screenshot":
                    result = await self.screenshot()
                elif action_type == "wait":
                    await self._browser.wait_for_timeout(params.get("ms", 2000))
                    result = True
                else:
                    logger.warning(f"Unknown action type: {action_type}")
                    result = None
            except Exception as e:
                logger.error(f"Step {i} failed ({action_type}): {e}")
                return {
                    "task": task_description,
                    "success": False,
                    "error": str(e),
                    "steps_completed": i,
                    "steps_total": len(steps),
                }

        return {
            "task": task_description,
            "success": True,
            "steps_completed": len(steps[:self._max_steps]),
            "steps_total": len(steps),
            "history": [
                {
                    "action": s.action.type,
                    "params": s.action.params,
                    "observation": s.observation,
                    "completed": s.completed,
                }
                for s in self._history
            ],
        }

    def get_history(self) -> List[dict]:
        return [
            {
                "action": s.action.type,
                "params": s.action.params,
                "observation": s.observation,
                "completed": s.completed,
                "error": s.error,
            }
            for s in self._history
        ]

    async def close(self):
        if self._browser:
            await self._browser.shutdown()
            self._browser = None
