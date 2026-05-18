import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class StepType(Enum):
    CLICK = "click"
    TYPE = "type"
    HOTKEY = "hotkey"
    SCREENSHOT = "screenshot"
    LOCATE = "locate"
    WAIT = "wait"
    SCROLL = "scroll"
    DRAG = "drag"
    MOVE = "move"
    EXTRACT_TEXT = "extract_text"
    THINK = "think"


@dataclass
class AutomationStep:
    step_type: StepType
    params: dict = field(default_factory=dict)
    description: str = ""

    @classmethod
    def click(cls, x: int, y: int, button: str = "left", desc: str = "") -> "AutomationStep":
        return cls(StepType.CLICK, {"x": x, "y": y, "button": button}, desc or f"Click ({x},{y})")

    @classmethod
    def type(cls, text: str, desc: str = "") -> "AutomationStep":
        return cls(StepType.TYPE, {"text": text}, desc or f"Type: {text[:30]}...")

    @classmethod
    def screenshot(cls, desc: str = "") -> "AutomationStep":
        return cls(StepType.SCREENSHOT, {}, desc or "Screenshot")

    @classmethod
    def wait(cls, seconds: float, desc: str = "") -> "AutomationStep":
        return cls(StepType.WAIT, {"seconds": seconds}, desc or f"Wait {seconds}s")

    @classmethod
    def think(cls, reasoning: str) -> "AutomationStep":
        return cls(StepType.THINK, {"reasoning": reasoning}, f"Think: {reasoning[:60]}...")


@dataclass
class StepResult:
    success: bool
    data: Any = None
    error: str = ""


class GUIAgent:
    def __init__(self, llm_callback: Optional[Callable] = None):
        self.llm = llm_callback

    async def execute(self, plan: list[dict]) -> list[StepResult]:
        results = []
        for step_dict in plan:
            step = AutomationStep(**step_dict)
            result = await self._run_step(step)
            results.append(result)
            if not result.success and step.step_type not in (StepType.THINK, StepType.WAIT):
                break
        return results

    async def _run_step(self, step: AutomationStep) -> StepResult:
        try:
            from nikto.cua import screen as scr, input as inp

            st = step.step_type
            p = step.params

            if st == StepType.CLICK:
                inp.click_at(p["x"], p["y"], p.get("button", "left"))
                return StepResult(True, f"Clicked ({p['x']},{p['y']})")

            elif st == StepType.TYPE:
                inp.type_text(p["text"])
                return StepResult(True, f"Typed {len(p['text'])} chars")

            elif st == StepType.HOTKEY:
                inp.hotkey(*p.get("keys", []))
                return StepResult(True, f"Pressed {p.get('keys', [])}")

            elif st == StepType.SCREENSHOT:
                path = scr.screenshot()
                return StepResult(True, path)

            elif st == StepType.LOCATE:
                box = scr.ScreenController().locate_on_screen(p.get("image"))
                return StepResult(box is not None, box)

            elif st == StepType.WAIT:
                await asyncio.sleep(p.get("seconds", 1))
                return StepResult(True, f"Waited {p.get('seconds', 1)}s")

            elif st == StepType.SCROLL:
                inp.scroll(p.get("clicks", 0))
                return StepResult(True, f"Scrolled {p.get('clicks', 0)}")

            elif st == StepType.DRAG:
                inp.drag(p["x"], p["y"])
                return StepResult(True, f"Dragged ({p['x']},{p['y']})")

            elif st == StepType.MOVE:
                inp.move_mouse(p["x"], p["y"])
                return StepResult(True, f"Moved to ({p['x']},{p['y']})")

            elif st == StepType.THINK:
                return StepResult(True, f"Thought: {p.get('reasoning', '')}")

            elif st == StepType.EXTRACT_TEXT:
                return StepResult(False, "OCR not implemented")

            return StepResult(False, f"Unknown step type: {st}")

        except Exception as e:
            logger.error(f"Step failed: {step.description}: {e}")
            return StepResult(False, error=str(e))
