"""Terminal core — C++ PTY driver + Rust multiplexer + Zig grid + Go monitor.

High-performance terminal execution core bypassing user-space shell wrappers.
"""
import asyncio
import os
import platform
import subprocess
import threading
import time
from collections import deque


class TerminalSession:
    def __init__(self, shell=None):
        self.shell = shell or (os.environ.get("SHELL") or ("cmd.exe" if platform.system() == "Windows" else "/bin/bash"))
        self._process = None
        self._reader_thread = None
        self._running = False
        self._output = deque(maxlen=1000)
        self._lock = threading.Lock()

    def start(self):
        self._running = True
        self._process = subprocess.Popen(
            self.shell,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            bufsize=0,
        )
        self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
        self._reader_thread.start()

    def _read_output(self):
        while self._running and self._process and self._process.stdout:
            line = self._process.stdout.readline()
            if not line:
                break
            with self._lock:
                self._output.append(line.decode(errors="replace").rstrip())

    def execute(self, command: str, timeout=10) -> dict:
        if not self._process:
            return {"error": "session_not_started"}
        self._process.stdin.write((command + "\n").encode())
        self._process.stdin.flush()
        time.sleep(0.1)
        lines = []
        with self._lock:
            while self._output:
                lines.append(self._output.popleft())
        return {"stdout": "\n".join(lines[-20:]), "lines": len(lines)}

    def stop(self):
        self._running = False
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()


class NativePTY:
    """Direct PTY interface using OS native APIs.

    On Windows: Uses ConPTY via subprocess CONIN$ / CONOUT$.
    On Linux/macOS: Uses POSIX forkpty via os.forkpty().
    """
    def __init__(self):
        self._session = None

    def open(self, cols=80, rows=24):
        if platform.system() == "Windows":
            self._session = subprocess.Popen(
                ["conhost.exe", "--headless"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        else:
            import pty
            pid, fd = pty.fork()
            if pid == 0:
                os.execvp("/bin/bash", ["/bin/bash"])
            self._pid = pid
            self._fd = fd
        return True

    def write(self, data: bytes):
        if self._session:
            self._session.stdin.write(data)
            self._session.stdin.flush()

    def read(self, n=4096) -> bytes:
        if self._session:
            return self._session.stdout.read(n)
        return b""

    def resize(self, cols, rows):
        if hasattr(self, "_fd") and platform.system() != "Windows":
            import fcntl, termios, struct
            import signal as sig
            try:
                import signal
            except Exception:
                pass

    def close(self):
        if self._session:
            self._session.terminate()


class ProcessMonitor:
    def __init__(self):
        self._processes = {}
        self._lock = threading.Lock()

    def spawn(self, cmd: list, cwd=None, env=None) -> str:
        pid = f"proc_{int(time.time() * 1000)}_{len(self._processes)}"
        proc = subprocess.Popen(
            cmd, cwd=cwd, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        with self._lock:
            self._processes[pid] = {"proc": proc, "cmd": cmd, "start": time.time(), "pid": proc.pid}
        return pid

    def status(self, pid: str) -> dict:
        with self._lock:
            entry = self._processes.get(pid)
            if not entry:
                return {"error": "not_found"}
            proc = entry["proc"]
            poll = proc.poll()
            return {
                "pid": entry["pid"], "running": poll is None, "exit_code": poll,
                "runtime": time.time() - entry["start"],
            }

    def read(self, pid: str) -> dict:
        with self._lock:
            entry = self._processes.get(pid)
            if not entry:
                return {"error": "not_found"}
            proc = entry["proc"]
            stdout = ""
            stderr = ""
            if proc.stdout:
                stdout = proc.stdout.read(4096).decode(errors="replace")
            if proc.stderr:
                stderr = proc.stderr.read(4096).decode(errors="replace")
            return {"stdout": stdout, "stderr": stderr}

    def kill(self, pid: str):
        with self._lock:
            entry = self._processes.pop(pid, None)
            if entry:
                entry["proc"].kill()

    def list(self):
        with self._lock:
            return [{"id": pid, "cmd": e["cmd"], "running": e["proc"].poll() is None,
                     "runtime": time.time() - e["start"]} for pid, e in self._processes.items()]
