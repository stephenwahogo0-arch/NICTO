from enum import Enum
from uuid import uuid4


class StepType(Enum):
    CLICK = "click"
    TYPE = "type"
    THINK = "think"
    SCREENSHOT = "screenshot"
    WAIT = "wait"


class AutomationStep:
    def __init__(self, step_type: StepType, params: dict = None):
        self.id = str(uuid4())[:12]
        self.step_type = step_type
        self.params = params or {}

    @classmethod
    def click(cls, x: int, y: int, button: str = "left") -> "AutomationStep":
        return cls(StepType.CLICK, {"x": x, "y": y, "button": button})

    @classmethod
    def type(cls, text: str) -> "AutomationStep":
        return cls(StepType.TYPE, {"text": text})

    @classmethod
    def think(cls, prompt: str) -> "AutomationStep":
        return cls(StepType.THINK, {"prompt": prompt})

    @classmethod
    def screenshot(cls) -> "AutomationStep":
        return cls(StepType.SCREENSHOT, {})

    @classmethod
    def wait(cls, seconds: float = 1.0) -> "AutomationStep":
        return cls(StepType.WAIT, {"seconds": seconds})
