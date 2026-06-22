import os
import ast
from uuid import uuid4


class CodeSecurityProtocol:
    def __init__(self):
        self.scan_id = str(uuid4())[:12]

    async def scan_code(self, path: str) -> dict:
        issues = []
        if not os.path.exists(path):
            return {"success": False, "error": f"Path not found: {path}"}
        if os.path.isfile(path) and path.endswith(".py"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler) and node.type is None:
                        issues.append({"type": "bare_except", "line": node.lineno, "severity": "medium"})
                    if isinstance(node, ast.Call) and hasattr(node.func, "attr") and node.func.attr in ("eval", "exec"):
                        issues.append({"type": "dangerous_call", "line": node.lineno, "severity": "high", "name": node.func.attr})
            except SyntaxError as e:
                issues.append({"type": "syntax_error", "error": str(e), "severity": "high"})
        try:
            import bandit
        except ImportError:
            pass
        return {"success": True, "scan_id": self.scan_id, "path": path, "issues": issues, "total": len(issues)}
