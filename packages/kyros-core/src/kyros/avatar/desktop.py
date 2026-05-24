"""Desktop control — open apps, type, move mouse, manage windows."""
import os
import subprocess
import time
from typing import Optional

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    import pygetwindow as gw
    PYGETWINDOW_AVAILABLE = True
except ImportError:
    PYGETWINDOW_AVAILABLE = False


class DesktopController:
    def __init__(self):
        self.last_typed = ""
        self.last_app = ""
        pyautogui.FAILSAFE = False

    def type_text(self, text: str, interval: float = 0.02) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"success": False, "error": "pyautogui not available"}
        try:
            pyautogui.write(text, interval=interval)
            self.last_typed = text[:100]
            return {"success": True, "characters": len(text)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def press_key(self, key: str) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"success": False, "error": "pyautogui not available"}
        try:
            pyautogui.press(key)
            return {"success": True, "key": key}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def hotkey(self, *keys) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"success": False, "error": "pyautogui not available"}
        try:
            pyautogui.hotkey(*keys)
            return {"success": True, "keys": keys}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def move_mouse(self, x: int, y: int, duration: float = 0.3) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"success": False, "error": "pyautogui not available"}
        try:
            screen_w, screen_h = pyautogui.size()
            x = max(0, min(x, screen_w - 1))
            y = max(0, min(y, screen_h - 1))
            pyautogui.moveTo(x, y, duration=duration)
            return {"success": True, "x": x, "y": y}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left") -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"success": False, "error": "pyautogui not available"}
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y, button=button)
            else:
                pyautogui.click(button=button)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_app(self, app_name: str) -> dict:
        try:
            if os.name == "nt":
                subprocess.Popen(["start", app_name], shell=True)
            elif os.name == "posix":
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen([app_name])
            self.last_app = app_name
            time.sleep(0.5)
            return {"success": True, "app": app_name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_url(self, url: str) -> dict:
        try:
            import webbrowser
            webbrowser.open(url)
            return {"success": True, "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_screenshot(self, path: Optional[str] = None) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"success": False, "error": "pyautogui not available"}
        try:
            screenshot = pyautogui.screenshot()
            if path:
                screenshot.save(path)
            return {"success": True, "size": screenshot.size, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_windows(self) -> dict:
        if not PYGETWINDOW_AVAILABLE:
            return {"success": False, "error": "pygetwindow not available"}
        try:
            windows = gw.getAllTitles()
            visible = [w for w in windows if w.strip()]
            return {"success": True, "windows": visible, "count": len(visible)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def focus_window(self, title: str) -> dict:
        if not PYGETWINDOW_AVAILABLE:
            return {"success": False, "error": "pygetwindow not available"}
        try:
            matching = gw.getWindowsWithText(title)
            if matching:
                matching[0].activate()
                return {"success": True, "window": title}
            return {"success": False, "error": f"No window found matching '{title}'"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_screen_size(self) -> dict:
        if not PYAUTOGUI_AVAILABLE:
            return {"success": False, "error": "pyautogui not available"}
        w, h = pyautogui.size()
        return {"success": True, "width": w, "height": h}

    def summary(self) -> dict:
        return {
            "pyautogui_available": PYAUTOGUI_AVAILABLE,
            "pygetwindow_available": PYGETWINDOW_AVAILABLE,
            "last_typed": self.last_typed[:50] if self.last_typed else "",
            "last_app": self.last_app,
        }