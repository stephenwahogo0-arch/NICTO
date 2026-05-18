import logging
from typing import Optional

import pyautogui
import pyperclip

logger = logging.getLogger(__name__)


def click_at(x: int, y: int, button: str = "left", clicks: int = 1, duration: float = 0.1):
    pyautogui.click(x=x, y=y, button=button, clicks=clicks, duration=duration)


def move_mouse(x: int, y: int, duration: float = 0.3):
    pyautogui.moveTo(x, y, duration=duration)


def type_text(text: str, interval: float = 0.02):
    pyautogui.typewrite(text, interval=interval)


def press_key(key: str, presses: int = 1):
    pyautogui.press(key, presses=presses)


def hotkey(*keys: str):
    pyautogui.hotkey(*keys)


def scroll(clicks: int, x: Optional[int] = None, y: Optional[int] = None):
    pyautogui.scroll(clicks, x=x, y=y)


def drag(x: int, y: int, duration: float = 0.3, button: str = "left"):
    pyautogui.drag(x, y, duration=duration, button=button)


def copy_text() -> str:
    return pyperclip.paste()


def paste_text(text: str):
    pyperclip.copy(text)


class InputController:
    def click(self, x: int, y: int, button: str = "left", clicks: int = 1):
        click_at(x, y, button, clicks)

    def move(self, x: int, y: int):
        move_mouse(x, y)

    def type(self, text: str):
        type_text(text)

    def press(self, key: str):
        press_key(key)

    def combo(self, *keys: str):
        hotkey(*keys)

    def scroll(self, clicks: int):
        scroll(clicks)

    def get_clipboard(self) -> str:
        return copy_text()

    def set_clipboard(self, text: str):
        paste_text(text)
