"""Intira Search — web search powered by Intira Browser + Chromium."""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus


logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    content: str = ""
    source: str = "web"
    position: int = 0
    relevance_score: float = 0.0
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntiraSearch:
    """Web search engine powered by Intira Browser + Chromium.

    Uses the Intira Browser to perform searches against major search engines,
    parse results, and extract content — all through a real Chromium browser.
    """

    SEARCH_ENGINES = {
        "duckduckgo": {
            "url": "https://html.duckduckgo.com/html/?q={query}",
            "result_selector": ".result",
            "title_selector": ".result__title a",
            "snippet_selector": ".result__snippet",
            "url_extract": "uddg",
        },
        "bing": {
            "url": "https://www.bing.com/search?q={query}&count={count}",
            "result_selector": "li.b_algo",
            "title_selector": "h2 a",
            "snippet_selector": ".b_caption p",
            "url_extract": None,
        },
        "brave": {
            "url": "https://search.brave.com/search?q={query}&count={count}",
            "result_selector": "div.snippet",
            "title_selector": "a.snippet-title",
            "snippet_selector": "div.snippet-description",
            "url_extract": None,
        },
    }

    def __init__(self, browser=None):
        self._browser = browser

    async def search(
        self,
        query: str,
        count: int = 10,
        engine: str = "duckduckgo",
        extract_content: bool = True,
        max_content_length: int = 5000,
    ) -> List[SearchResult]:
        """Search the web using Intira Browser + Chromium."""
        if self._browser is None:
            from .browser import IntiraBrowser
            self._browser = IntiraBrowser(headless=True)
            await self._browser.launch()

        engine_config = self.SEARCH_ENGINES.get(engine)
        if not engine_config:
            logger.warning(f"Unknown engine '{engine}', falling back to duckduckgo")
            engine_config = self.SEARCH_ENGINES["duckduckgo"]
            engine = "duckduckgo"

        url = engine_config["url"].format(query=quote_plus(query), count=count)
        logger.info(f"Intira Search [{engine}]: {query[:80]}...")

        try:
            await self._browser.navigate(url)
            await self._browser.wait_for_timeout(3000)

            try:
                await self._browser.page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass

            html = await self._browser.get_page_html()
            results = self._parse_html(
                html, engine_config, engine, query
            )

            if extract_content and results:
                await self._extract_contents(results, max_content_length)

            logger.info(f"Intira Search: {len(results)} results for \"{query[:60]}\"")
            return results

        except Exception as e:
            logger.error(f"Intira Search failed: {e}")
            return []

    def _parse_html(
        self, html: str, config: dict, engine: str, query: str
    ) -> List[SearchResult]:
        """Parse search engine HTML into structured results."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
        except Exception as e:
            logger.warning(f"HTML parsing failed: {e}")
            return []

        results = []
        for i, elem in enumerate(soup.select(config["result_selector"])):
            try:
                title_elem = elem.select_one(config["title_selector"])
                snippet_elem = (
                    elem.select_one(config["snippet_selector"])
                    if config["snippet_selector"]
                    else None
                )

                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = title_elem.get("href", "")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                url = self._resolve_url(url, config.get("url_extract"))

                if title and url:
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source=engine,
                        position=i + 1,
                        timestamp=time.time(),
                    ))
            except Exception:
                continue

        return results

    def _resolve_url(self, url: str, extract_param: Optional[str]) -> str:
        """Resolve search engine redirect URLs to real URLs."""
        import urllib.parse
        if url.startswith("//"):
            url = "https:" + url
        if extract_param:
            parsed = urllib.parse.urlparse(url)
            if parsed.hostname:
                qs = urllib.parse.parse_qs(parsed.query)
                if extract_param in qs:
                    return qs[extract_param][0]
        return url

    async def _extract_contents(
        self, results: List[SearchResult], max_length: int
    ):
        """Extract full page content for each search result."""
        for result in results:
            try:
                await self._browser.navigate(result.url)
                await self._browser.wait_for_timeout(2000)

                text = await self._browser.execute_script("""
                    () => {
                        const article = document.querySelector('article');
                        if (article) return article.innerText;
                        const main = document.querySelector('main');
                        if (main) return main.innerText;
                        const body = document.body;
                        if (body) return body.innerText;
                        return '';
                    }
                """)

                if text and len(text.strip()) > 50:
                    import re
                    result.content = re.sub(r'\s+', ' ', text).strip()[:max_length]
                else:
                    html = await self._browser.get_page_html()
                    result.content = self._extract_readable(html)[:max_length]

                await self._browser.wait_for_timeout(300)
            except Exception as e:
                logger.debug(f"Content extraction failed for {result.url}: {e}")

    def _extract_readable(self, html: str) -> str:
        """Extract readable text from HTML."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "lxml")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            return soup.get_text(separator=" ", strip=True)
        except Exception:
            return ""

    async def fetch_page(self, url: str, max_length: int = 5000) -> str:
        """Fetch and extract content from a single URL."""
        if self._browser is None:
            from .browser import IntiraBrowser
            self._browser = IntiraBrowser(headless=True)
            await self._browser.launch()

        try:
            await self._browser.navigate(url)
            await self._browser.wait_for_timeout(2000)

            text = await self._browser.get_page_text()
            if text and len(text.strip()) > 50:
                import re
                return re.sub(r'\s+', ' ', text).strip()[:max_length]

            html = await self._browser.get_page_html()
            return self._extract_readable(html)[:max_length]
        except Exception as e:
            logger.error(f"Fetch page failed for {url}: {e}")
            return ""

    async def close(self):
        if self._browser:
            await self._browser.shutdown()
            self._browser = None

    @property
    def page(self):
        return self._browser._page if self._browser else None
