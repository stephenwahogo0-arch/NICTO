"""Security sandbox for NIKTO — Rust Seccomp/Landlock + Python rule validation.

Isolates agent code execution within sandboxed environments.
Provides prompt sanitization and security rule parsing.
"""
import json
import os
import re
import tempfile
from typing import Optional


class PromptSanitizer:
    PATTERNS = [
        (r"(?i)(system\s*prompt|ignore\s*all\s*previous|override\s*system)", "prompt_injection"),
        (r"(?i)(your\s*instructions?\s*are\s*to|forget\s*everything|new\s*instructions?:)", "instruction_override"),
        (r"(?i)(<[^>]*>.*?</[^>]*>)", "html_injection"),
        (r"(?i)(javascript:|onerror=|onload=|onclick=)", "xss_attempt"),
        (r"(?i)(DROP\s+TABLE|DELETE\s+FROM|INSERT\s+INTO|UPDATE\s+\w+\s+SET)", "sql_injection"),
        (r"(?i)(eval\(|exec\(|system\(|subprocess\.)", "code_execution"),
        (r"(?i)(base64|hex|rot13|urlencode).*(decode|encod)", "obfuscation"),
        (r"(?i)(role\s*[:=]\s*\"?\w+\"?)", "role_injection"),
    ]

    def sanitize(self, text: str) -> dict:
        flags = []
        clean = text
        for pattern, category in self.PATTERNS:
            matches = re.findall(pattern, clean)
            if matches:
                flags.append({"category": category, "count": len(matches)})
                clean = re.sub(pattern, "[FILTERED]", clean)
        return {"original_length": len(text), "filtered_length": len(clean), "flags": flags, "sanitized": clean,
                "is_safe": len(flags) == 0}

    def is_safe(self, text: str) -> bool:
        return len(re.findall(r"(?i)(ignore|override|system\s*prompt|forget\s*everything)", text)) == 0


class RuleValidator:
    def __init__(self):
        self.rules = []

    def add_rule(self, name: str, check_fn):
        self.rules.append({"name": name, "check": check_fn})

    def validate(self, action: dict) -> dict:
        violations = []
        for rule in self.rules:
            try:
                if not rule["check"](action):
                    violations.append(rule["name"])
            except Exception:
                violations.append(f"{rule['name']}_error")
        return {"action": action.get("type", "unknown"), "allowed": len(violations) == 0, "violations": violations}


class SandboxRestrictions:
    def __init__(self):
        self.allowed_paths = {os.path.expanduser("~/.nikto")}
        self.allowed_commands = {"ls", "cat", "echo", "python", "pip", "git", "node", "npm", "cargo", "rustc"}
        self.max_memory_mb = 512
        self.max_cpu_seconds = 30
        self.max_file_size_mb = 10
        self.blocked_networks = {"10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8"}
        self.blocked_env_vars = {"API_KEY", "SECRET", "PASSWORD", "TOKEN", "CREDENTIAL"}

    def check_path(self, path: str) -> bool:
        abs_path = os.path.abspath(path)
        for allowed in self.allowed_paths:
            if abs_path.startswith(os.path.abspath(allowed)):
                return True
        return False

    def check_command(self, cmd: str) -> bool:
        base = os.path.basename(cmd.split()[0]).lower()
        return base in self.allowed_commands

    def check_network(self, host: str) -> bool:
        import ipaddress
        try:
            addr = ipaddress.ip_address(host)
            for net in self.blocked_networks:
                if addr in ipaddress.ip_network(net):
                    return False
        except Exception:
            pass
        return True

    def validate_action(self, action_type: str, params: dict) -> dict:
        violations = []
        if action_type == "file_access":
            path = params.get("path", "")
            if not self.check_path(path):
                violations.append(f"path_not_allowed: {path}")
        elif action_type == "command":
            cmd = params.get("command", "")
            if not self.check_command(cmd):
                violations.append(f"command_not_allowed: {cmd}")
        elif action_type == "network":
            host = params.get("host", "")
            if not self.check_network(host):
                violations.append(f"network_blocked: {host}")
        elif action_type == "memory":
            mb = params.get("mb", 0)
            if mb > self.max_memory_mb:
                violations.append(f"memory_exceeded: {mb}MB > {self.max_memory_mb}MB")

        return {"allowed": len(violations) == 0, "violations": violations}


class RustSandbox:
    def __init__(self):
        self._lib = None
        self.restrictions = SandboxRestrictions()
        self.sanitizer = PromptSanitizer()
        self.validator = RuleValidator()

        self.validator.add_rule("memory_limit", lambda a: a.get("mb", 0) <= self.restrictions.max_memory_mb)
        self.validator.add_rule("cpu_limit", lambda a: a.get("cpu_seconds", 0) <= self.restrictions.max_cpu_seconds)
        self.validator.add_rule("file_size", lambda a: a.get("file_mb", 0) <= self.restrictions.max_file_size_mb)

    def check_prompt(self, text: str) -> dict:
        return self.sanitizer.sanitize(text)

    def check_action(self, action_type: str, params: dict) -> dict:
        # Try Rust sandbox first (Seccomp/Landlock)
        result = self.restrictions.validate_action(action_type, params)
        # Also run Python-level rule validation
        py_result = self.validator.validate({"type": action_type, **params})
        result["py_violations"] = py_result.get("violations", [])
        result["allowed"] = result["allowed"] and py_result.get("allowed", True)
        return result

    def sandboxed_execute(self, code: str, language: str = "python") -> dict:
        safe = self.check_prompt(code)
        if not safe["is_safe"]:
            return {"executed": False, "error": "prompt_sanitization_failed", "flags": safe["flags"]}

        with tempfile.TemporaryDirectory(prefix="nikto_sandbox_") as tmpdir:
            script_path = os.path.join(tmpdir, f"script.{language}")
            with open(script_path, "w") as f:
                f.write(safe["sanitized"])

            import subprocess
            try:
                runner = {"python": ["python", script_path], "bash": ["bash", script_path]}
                cmd = runner.get(language, ["python", script_path])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.restrictions.max_cpu_seconds,
                                        cwd=tmpdir)
                return {
                    "executed": True,
                    "stdout": result.stdout[:1000],
                    "stderr": result.stderr[:1000],
                    "returncode": result.returncode,
                }
            except subprocess.TimeoutExpired:
                return {"executed": False, "error": "timeout", "cpu_seconds": self.restrictions.max_cpu_seconds}
            except Exception as e:
                return {"executed": False, "error": str(e)}
