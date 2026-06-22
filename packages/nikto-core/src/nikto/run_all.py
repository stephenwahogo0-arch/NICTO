"""Unified launcher — starts a single Nikto server handling all 4 models (Kyros, Omega, Main, X)."""

import os
import sys
import time
import json
import signal
import logging
import subprocess
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nikto.launcher")

NIKTO_PORT = 5000

processes: list[subprocess.Popen] = []


def start_server(port: int, no_auth: bool = False):
    script = Path(__file__).parent / "server.py"
    if not script.exists():
        alt = os.path.join(os.path.dirname(__file__), "server.py")
        if os.path.exists(alt):
            script = Path(alt)
        else:
            logger.error(f"Server script not found at {script} or {alt}")
            return None

    cmd = [sys.executable, str(script), "--port", str(port)]
    if no_auth:
        cmd.append("--no-auth")

    logger.info(f"Starting Nikto unified server on port {port}...")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append(proc)
    return proc


def stop_all(signum=None, frame=None):
    logger.info("Shutting down server...")
    for proc in processes:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
    logger.info("Server stopped.")


def main():
    no_auth = "--no-auth" in sys.argv

    signal.signal(signal.SIGINT, stop_all)
    signal.signal(signal.SIGTERM, stop_all)

    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║         NICTO UNIFIED SYSTEM LAUNCHER        ║")
    print("  ╠══════════════════════════════════════════════╣")
    print(f"  ║  All models → http://127.0.0.1:{NIKTO_PORT}             ║")
    print("  ║                                              ║")
    print("  ║  Models:                                     ║")
    print("  ║    ⚡  Kyros   — Minimal (identity+memory)   ║")
    print("  ║    ⚖️   Omega   — Core reasoning              ║")
    print("  ║    🔧  Main    — Full-featured               ║")
    print("  ║    🚀  X       — Frontier agents              ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()

    proc = start_server(NIKTO_PORT, no_auth)

    if not proc:
        logger.error("Failed to start server.")
        sys.exit(1)

    logger.info(f"Nikto unified server running on port {NIKTO_PORT}")
    logger.info("Send X-Model-Id header: nicto_kyros | nicto_omega | nicto_main | nicto_x")
    logger.info("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
            if proc.poll() is not None:
                logger.warning(f"Server exited (code {proc.returncode})")
                break
    except KeyboardInterrupt:
        stop_all()


if __name__ == "__main__":
    main()
