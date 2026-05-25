"""Action planner — maps reasoning outputs to concrete actions."""


class ActionPlanner:
    """Maps brain outputs to concrete executable actions."""

    def __init__(self, tool_registry):
        self.tools = tool_registry
        self._action_history: list[dict] = []

    def plan_actions(self, task: str, brain_output: dict) -> list[dict]:
        """Convert brain output into a sequence of executable actions."""
        actions = []
        confidence = brain_output.get("confidence", 0.5)

        if isinstance(confidence, (int, float)):
            conf_val = float(confidence)
        else:
            conf_val = 0.5

        if conf_val > 0.8:
            actions.append({
                "type": "execute",
                "tool": "shell_exec",
                "priority": 1.0,
                "description": f"Execute high-confidence action for: {task[:50]}",
            })
        elif conf_val > 0.5:
            actions.append({
                "type": "research",
                "tool": "web_search",
                "priority": 0.7,
                "description": f"Research before acting: {task[:50]}",
            })
            actions.append({
                "type": "execute",
                "tool": "shell_exec",
                "priority": 0.6,
                "description": f"Execute with verification: {task[:50]}",
            })
        else:
            actions.append({
                "type": "clarify",
                "tool": None,
                "priority": 0.5,
                "description": "Low confidence — request clarification",
            })

        self._action_history.extend(actions)
        return actions

    def execute_action(self, action: dict) -> dict:
        """Execute a single action."""
        if action.get("tool") is None:
            return {"status": "skipped", "reason": "no tool specified"}
        return self.tools.execute(action["tool"])

    def get_history(self, limit: int = 20) -> list[dict]:
        return self._action_history[-limit:]
