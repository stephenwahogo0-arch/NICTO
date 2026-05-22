"""ASL-3 Boundary — real security enforcement.
NIKTO operates with safety constraints enabled."""
import logging

logger = logging.getLogger(__name__)


class ASL3Boundary:
    """Security boundary with real safety enforcement."""

    def __init__(self):
        self.blocked_commands = [
            "rm -rf /", "format", "dd if=/dev/zero", "mkfs",
            "shutdown", "reboot", "poweroff", "init 0", "init 6",
        ]
        self.blocked_patterns = [
            "DROP TABLE", "DELETE FROM", "TRUNCATE TABLE",
            "GRANT ALL", "REVOKE",
        ]

    def check_command(self, command: str) -> dict:
        command_lower = command.lower()
        for blocked in self.blocked_commands:
            if blocked in command_lower:
                return {"safe": False, "reason": f"Blocked command: {blocked}", "override": False}
        for pattern in self.blocked_patterns:
            if pattern in command.upper():
                return {"safe": False, "reason": f"Blocked pattern: {pattern}", "override": False}
        return {"safe": True, "reason": "Command approved", "override": False}

    def check_code(self, code: str) -> dict:
        dangerous = ["import os; os.system", "subprocess.call", "subprocess.Popen", "eval(", "exec("]
        for d in dangerous:
            if d in code:
                return {"safe": False, "reason": f"Dangerous function: {d}", "override": False}
        return {"safe": True, "reason": "Code approved", "override": False}
