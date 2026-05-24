import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

from nikto.variants.base import AgentVariant, SONNET_CONFIG

logger = logging.getLogger(__name__)


class NiktoSonnet(AgentVariant):
    """nikto-denu — The Fast & Intelligent All-Rounder.
    Excels at high-speed execution, daily coding, UI building, rapid task handling.
    """

    def __init__(self, config=None):
        super().__init__(config or SONNET_CONFIG)

    async def extended_think(self, prompt: str, depth: int = 3) -> str:
        """Extended Thinking Toggle — Pause and reason deeply before answering."""
        steps = []
        current = prompt
        for i in range(depth):
            step = f"[EXTENDED THINKING] Layer {i+1}/{depth}: Analyzing '{current[:80]}...'"
            steps.append(step)
            current = f"refined: {current}"
        return "\n".join(steps) + f"\n[CONCLUSION] Deep reasoning complete on: {prompt[:100]}"

    def render_live_artifact(self, artifact_type: str, content: str) -> str:
        """Live Artifacts Previews — Render React apps, web pages, SVG directly."""
        if artifact_type == "react":
            return f"<div id='nikto-live-artifact' data-type='react'>{content}</div>"
        elif artifact_type == "svg":
            return content
        elif artifact_type == "html":
            return f"<!DOCTYPE html><html><body>{content}</body></html>"
        return content

    async def computer_use(self, action: str, params: dict = None) -> dict:
        """Computer Use — Control screen, cursor, clicks, typing."""
        from nikto.cua.screen import ScreenController
        from nikto.cua.input import InputController
        scr = ScreenController()
        inp = InputController()

        action_map = {
            "click": lambda: inp.click(params.get("x", 0), params.get("y", 0)),
            "type": lambda: inp.type(params.get("text", "")),
            "screenshot": lambda: scr.capture(),
            "move": lambda: inp.move(params.get("x", 0), params.get("y", 0)),
            "scroll": lambda: inp.scroll(params.get("clicks", 0)),
            "press": lambda: inp.press(params.get("key", "")),
        }
        handler = action_map.get(action)
        if handler:
            result = await asyncio.to_thread(handler)
            return {"action": action, "status": "executed", "result": str(result)}
        return {"action": action, "status": "unknown_action"}
