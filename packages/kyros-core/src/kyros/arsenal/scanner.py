"""Cybersecurity Arsenal — native Go network scanner with Python fallback.

Zero external tool dependencies (no Nmap, no Gobuster, no Metasploit).
Uses Go's stdlib net package for native TCP scans via subprocess.
"""
import json
import os
import subprocess
from typing import Optional


class SecurityScanner:
    def __init__(self):
        self._go_path = None
        self._go_compiled = False
        self._locate_go_binary()

    def _locate_go_binary(self):
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..",
                         "packages", "nikto-super-kernel", "go", "scanner", "scanner.exe"),
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..",
                         "packages", "nikto-super-kernel", "go", "scanner", "scanner"),
        ]
        for path in candidates:
            if os.path.exists(path):
                self._go_path = path
                self._go_compiled = True
                return

    @property
    def available(self):
        return self._go_compiled and self._go_path is not None

    def ping(self, host: str) -> bool:
        if self.available:
            try:
                result = subprocess.run([self._go_path, "ping", host], capture_output=True, text=True, timeout=5)
                data = json.loads(result.stdout)
                return data.get("reached", False)
            except Exception:
                pass
        return self._python_ping(host)

    def scan(self, host: str, ports="common", timeout_ms=2000) -> dict:
        if self.available:
            try:
                args = [self._go_path, "scan", host]
                if ports:
                    args.append(ports)
                args.append(str(timeout_ms))
                result = subprocess.run(args, capture_output=True, text=True, timeout=30)
                data = json.loads(result.stdout)
                if "error" not in data:
                    return data
            except Exception:
                pass
        return self._python_scan(host, ports, timeout_ms)

    def _python_ping(self, host):
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((host, 80))
            s.close()
            return True
        except Exception:
            return False

    def _python_scan(self, host, ports, timeout_ms):
        import socket
        from concurrent.futures import ThreadPoolExecutor
        common = {21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
                  80: "http", 443: "https", 3306: "mysql", 3389: "rdp", 8080: "http-proxy"}
        if ports == "common":
            port_list = list(common.keys())
        else:
            port_list = [int(p.strip()) for p in ports.split(",") if p.strip().isdigit()]
        results = []
        timeout = timeout_ms / 1000.0

        def check(p):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                s.connect((host, p))
                s.close()
                results.append({"port": p, "open": True, "service": common.get(p, "unknown"), "banner": ""})
            except Exception:
                pass

        with ThreadPoolExecutor(max_workers=50) as ex:
            ex.map(check, port_list)

        return {"host": host, "ports": results, "open_count": len(results), "duration": "python_fallback"}

    def summarize(self, host: str) -> str:
        result = self.scan(host)
        lines = [f"Scan: {host}", "=" * 40]
        if "ports" in result:
            for p in result["ports"]:
                if p.get("open"):
                    lines.append(f"  PORT {p['port']:<5} OPEN  {p.get('service', 'unknown')}")
        lines.append(f"  Total open: {result.get('open_count', 0)}")
        if "duration" in result:
            lines.append(f"  Duration: {result['duration']}ms")
        return "\n".join(lines)
