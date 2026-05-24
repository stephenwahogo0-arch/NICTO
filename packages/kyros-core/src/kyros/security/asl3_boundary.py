from uuid import uuid4


class ASL3Boundary:
    def __init__(self):
        self.boundary_id = str(uuid4())[:12]

    def classify_and_filter(self, command: str, context: dict = None) -> object:
        class LogObject:
            def __init__(self):
                self.blocked = False
                self.classification = "safe"
                self.reason = ""
                self.risk_score = 0.0
        log = LogObject()
        dangerous_patterns = ["rm -rf /", "format", "shutdown", "reboot", "dd if="]
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                log.blocked = True
                log.classification = "dangerous_command"
                log.reason = f"Command contains blocked pattern: {pattern}"
                log.risk_score = 0.9
                break
        return log
