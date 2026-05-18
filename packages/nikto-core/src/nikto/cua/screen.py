import asyncio
import base64
import io
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    import mss
    _MSS_AVAILABLE = True
except ImportError:
    _MSS_AVAILABLE = False
    logger.warning("mss not installed; using pyautogui for screenshots")


def list_screens() -> list[dict]:
    if _MSS_AVAILABLE:
        with mss.mss() as sct:
            return [
                {"id": m["left"], "width": m["width"], "height": m["height"], "name": m.get("monitor", i)}
                for i, m in enumerate(sct.monitors)
            ]
    return [{"id": 0, "width": pyautogui.size().width, "height": pyautogui.size().height, "name": "primary"}]


def screenshot(region: tuple = None, as_base64: bool = False) -> str:
    if region:
        img = pyautogui.screenshot(region=region)
    else:
        img = pyautogui.screenshot()
    if as_base64:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    path = Path.home() / ".nikto" / "screenshots"
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / f"screen_{asyncio.get_event_loop().time():.0f}.png"
    img.save(filepath)
    return str(filepath)


class ScreenController:
    def __init__(self):
        pass

    def capture(self, region: tuple = None) -> str:
        return screenshot(region=region)

    def capture_b64(self, region: tuple = None) -> str:
        return screenshot(region=region, as_base64=True)

    def dimensions(self) -> tuple:
        return pyautogui.size()

    def pixel(self, x: int, y: int) -> tuple:
        return pyautogui.pixel(x, y)

    def locate_on_screen(self, image_path: str, confidence: float = 0.9) -> Optional[tuple]:
        return pyautogui.locateOnScreen(image_path, confidence=confidence)

    def locate_all(self, image_path: str, confidence: float = 0.9) -> list:
        return list(pyautogui.locateAllOnScreen(image_path, confidence=confidence))
