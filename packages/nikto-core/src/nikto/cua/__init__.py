"""Computer Use Agent (CUA) — real screen control, viewing, and automation.
Wraps PyAutoGUI, MSS, and keyboard/mouse simulation for full GUI agent capability."""
from nikto.cua.screen import ScreenController, screenshot, list_screens
from nikto.cua.input import InputController, type_text, press_key, click_at, move_mouse, scroll, drag
from nikto.cua.automation import GUIAgent, AutomationStep, StepResult

__all__ = [
    "ScreenController", "screenshot", "list_screens",
    "InputController", "type_text", "press_key", "click_at", "move_mouse", "scroll", "drag",
    "GUIAgent", "AutomationStep", "StepResult",
]
