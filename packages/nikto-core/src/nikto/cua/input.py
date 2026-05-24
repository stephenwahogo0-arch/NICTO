from nikto.tools.base import Tool


class InputController:
    def __init__(self):
        self._mouse = None
        self._keyboard = None

    def click(self, x: int, y: int, button: str = "left") -> dict:
        try:
            import pyautogui
            pyautogui.click(x, y, button=button)
            return {"success": True, "x": x, "y": y, "button": button}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def type_text(self, text: str) -> dict:
        try:
            import pyautogui
            pyautogui.typewrite(text)
            return {"success": True, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def press_key(self, key: str) -> dict:
        try:
            import pyautogui
            pyautogui.press(key)
            return {"success": True, "key": key}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def move_to(self, x: int, y: int) -> dict:
        try:
            import pyautogui
            pyautogui.moveTo(x, y)
            return {"success": True, "x": x, "y": y}
        except Exception as e:
            return {"success": False, "error": str(e)}
