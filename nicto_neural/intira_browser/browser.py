"""Intira Browser — NICTO's Chromium-based web browser core."""
import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from urllib.parse import urlparse, urljoin


logger = logging.getLogger(__name__)


STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
window.chrome = { runtime: {} };
const originalFetch = window.fetch;
"""

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Intira/1.0 Chrome/125.0.0.0 Safari/537.36"
INTIRA_VERSION = "1.0.0"


@dataclass
class IntiraTab:
    """Represents a browser tab within Intira."""
    tab_id: int
    url: str = "about:blank"
    title: str = "New Tab"
    status: str = "idle"
    created_at: float = 0.0
    history: List[str] = field(default_factory=list)
    page_content: str = ""
    screenshot_path: str = ""

    def navigate_to(self, url: str):
        self.history.append(self.url)
        self.url = url
        self.status = "loading"


@dataclass
class BrowserSession:
    """Persistent session data for Intira Browser."""
    cookies_file: str = ""
    local_storage: Dict[str, str] = field(default_factory=dict)
    session_data: Dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    last_active: float = 0.0


class IntiraBrowser:
    """Intira Browser — NICTO's Chromium-based browser engine.

    Provides full browser capabilities: tab management, navigation,
    JavaScript execution, form interaction, screenshot, content extraction,
    stealth anti-detection, and session persistence.
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 30000,
        data_dir: Optional[str] = None,
        window_width: int = 1280,
        window_height: int = 720,
    ):
        self.headless = headless
        self.timeout = timeout
        self.data_dir = data_dir or os.path.join(
            os.path.expanduser("~"), ".intira", "browser_data"
        )
        self.window_width = window_width
        self.window_height = window_height

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._tabs: Dict[int, IntiraTab] = {}
        self._active_tab_id: int = 0
        self._tab_counter: int = 0
        self._session: BrowserSession = None
        self._is_running: bool = False
        self._event_listeners: Dict[str, List[Callable]] = {}

    async def launch(self):
        """Launch the Intira Browser (Chromium instance)."""
        if self._is_running:
            return

        from playwright.async_api import async_playwright

        os.makedirs(self.data_dir, exist_ok=True)

        self._playwright = await async_playwright().start()
        launch_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-blink-features=AutomationControlled",
            f"--window-size={self.window_width},{self.window_height}",
            "--disable-infobars",
            "--disable-notifications",
            "--disable-popup-blocking",
        ]
        if self.headless:
            launch_args.append("--headless=new")

        self._browser = await self._playwright.chromium.launch(
            headless=False,
            args=launch_args,
        )

        self._context = await self._browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": self.window_width, "height": self.window_height},
            locale="en-US",
            timezone_id="America/New_York",
            permissions=["geolocation", "notifications"],
            ignore_https_errors=False,
            java_script_enabled=True,
        )

        self._page = await self._context.new_page()
        await self._page.add_init_script(STEALTH_SCRIPT)

        self._tab_counter += 1
        tab = IntiraTab(
            tab_id=self._tab_counter,
            url="about:blank",
            title="New Tab",
            status="idle",
            created_at=time.time(),
        )
        self._tabs[self._tab_counter] = tab
        self._active_tab_id = self._tab_counter

        self._session = BrowserSession(
            cookies_file=os.path.join(self.data_dir, "cookies.json"),
            created_at=time.time(),
            last_active=time.time(),
        )
        self._is_running = True

        await self._load_session()
        logger.info(f"Intira Browser v{INTIRA_VERSION} launched (PID: {self._browser})")

    async def new_tab(self, url: str = "about:blank") -> IntiraTab:
        """Open a new browser tab."""
        page = await self._context.new_page()
        await page.add_init_script(STEALTH_SCRIPT)

        self._tab_counter += 1
        tab = IntiraTab(
            tab_id=self._tab_counter,
            url=url,
            title=f"Tab {self._tab_counter}",
            status="idle",
            created_at=time.time(),
        )
        self._tabs[self._tab_counter] = tab
        self._active_tab_id = self._tab_counter
        self._page = page

        if url != "about:blank":
            await self.navigate(url)

        return tab

    async def navigate(self, url: str, tab_id: Optional[int] = None) -> str:
        """Navigate a tab to a URL. Returns the page title."""
        target_id = tab_id if tab_id is not None else self._active_tab_id
        tab = self._tabs.get(target_id)
        if not tab:
            raise ValueError(f"Tab {target_id} not found")

        if target_id != self._active_tab_id:
            raise NotImplementedError("Multi-tab navigation via tab_id not yet implemented")

        if not url.startswith(("http://", "https://", "file://")):
            url = "https://" + url

        tab.status = "loading"
        tab.navigate_to(url)

        try:
            await self._page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
            await self._page.wait_for_load_state("networkidle", timeout=min(self.timeout, 15000))
        except Exception:
            try:
                await self._page.wait_for_load_state("load", timeout=10000)
            except Exception:
                pass

        tab.title = await self._page.title() or url
        tab.page_content = await self._page.content()
        tab.status = "loaded"
        self._session.last_active = time.time()

        logger.info(f"Navigated to {url} — \"{tab.title}\"")
        return tab.title

    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript in the active tab."""
        return await self._page.evaluate(script)

    async def get_page_html(self) -> str:
        """Get the full HTML of the active page."""
        return await self._page.content()

    async def get_page_text(self) -> str:
        """Get visible text from the active page."""
        return await self._page.evaluate("() => document.body.innerText")

    async def get_page_title(self) -> str:
        """Get the title of the active page."""
        return await self._page.title()

    async def get_page_url(self) -> str:
        """Get the current URL of the active tab."""
        return self._page.url

    async def click(self, selector: str) -> bool:
        """Click an element on the page."""
        try:
            await self._page.click(selector, timeout=5000)
            return True
        except Exception as e:
            logger.debug(f"Click failed on '{selector}': {e}")
            return False

    async def fill_input(self, selector: str, value: str) -> bool:
        """Fill a form input field."""
        try:
            await self._page.fill(selector, value, timeout=5000)
            return True
        except Exception as e:
            logger.debug(f"Fill failed on '{selector}': {e}")
            return False

    async def select_option(self, selector: str, value: str) -> bool:
        """Select an option from a dropdown."""
        try:
            await self._page.select_option(selector, value)
            return True
        except Exception as e:
            logger.debug(f"Select failed on '{selector}': {e}")
            return False

    async def screenshot(self, path: Optional[str] = None) -> Optional[str]:
        """Take a screenshot of the active tab."""
        save_path = path or os.path.join(self.data_dir, f"screenshot_{int(time.time())}.png")
        try:
            await self._page.screenshot(path=save_path, full_page=True)
            if self._active_tab_id in self._tabs:
                self._tabs[self._active_tab_id].screenshot_path = save_path
            return save_path
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

    async def scroll_to(self, x: int = 0, y: int = 0):
        """Scroll the active page to coordinates."""
        await self._page.evaluate(f"window.scrollTo({x}, {y})")

    async def scroll_by(self, dx: int = 0, dy: int = 500):
        """Scroll the active page by offset."""
        await self._page.evaluate(f"window.scrollBy({dx}, {dy})")

    async def wait_for_selector(self, selector: str, timeout: int = 10000) -> bool:
        """Wait for an element to appear on the page."""
        try:
            await self._page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False

    async def wait_for_timeout(self, ms: int = 1000):
        """Wait for a specified time in milliseconds."""
        await self._page.wait_for_timeout(ms)

    async def get_links(self) -> List[Dict[str, str]]:
        """Get all links on the current page."""
        return await self._page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
                text: a.innerText.trim().slice(0, 100),
                href: a.href,
            }))
        """)

    async def get_network_requests(self) -> List[Dict[str, Any]]:
        """Get network requests made by the page (requires browser launch)."""
        requests = await self._page.evaluate("""
            () => performance.getEntriesByType('resource').map(e => ({
                url: e.name,
                duration: e.duration,
                type: e.initiatorType,
                size: e.transferSize,
            }))
        """)
        return requests

    async def close_tab(self, tab_id: Optional[int] = None):
        """Close a browser tab."""
        target_id = tab_id if tab_id is not None else self._active_tab_id
        if target_id in self._tabs:
            if len(self._tabs) <= 1:
                logger.warning("Cannot close the last tab")
                return
            del self._tabs[target_id]
            if self._active_tab_id == target_id:
                self._active_tab_id = next(iter(self._tabs.keys()))
            logger.info(f"Tab {target_id} closed")

    async def _load_session(self):
        """Restore session from disk."""
        if self._session and os.path.exists(self._session.cookies_file):
            try:
                with open(self._session.cookies_file, "r") as f:
                    cookies_data = json.load(f)
                if cookies_data:
                    await self._context.add_cookies(cookies_data)
                    logger.info(f"Restored {len(cookies_data)} cookies from session")
            except Exception as e:
                logger.warning(f"Failed to load session: {e}")

    async def _save_session(self):
        """Save session to disk."""
        if not self._session:
            return
        try:
            cookies = await self._context.cookies()
            with open(self._session.cookies_file, "w") as f:
                json.dump(cookies, f, indent=2)
            self._session.last_active = time.time()
            logger.info(f"Saved {len(cookies)} cookies to session")
        except Exception as e:
            logger.warning(f"Failed to save session: {e}")

    async def shutdown(self):
        """Shut down Intira Browser."""
        if not self._is_running:
            return

        await self._save_session()

        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None
        self._tabs.clear()
        self._is_running = False
        logger.info("Intira Browser shut down")

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the browser."""
        return {
            "running": self._is_running,
            "version": INTIRA_VERSION,
            "headless": self.headless,
            "active_tab": self._active_tab_id,
            "tabs_count": len(self._tabs),
            "tabs": [
                {"id": tid, "url": t.url, "title": t.title, "status": t.status}
                for tid, t in self._tabs.items()
            ],
            "session_active": self._session is not None,
            "data_dir": self.data_dir,
        }

    async def __aenter__(self):
        await self.launch()
        return self

    async def __aexit__(self, *args):
        await self.shutdown()
