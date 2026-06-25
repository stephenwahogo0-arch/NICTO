"""NICTO Desktop App — Python backend server.

Connects the Tauri/React desktop app to NICTO's 7-Brain MoE+MLA architecture.
Run this before launching the app:
  python packages/nikto-app/server.py
"""

import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

os.environ["NIKTO_ENABLE_EXPERIMENTAL"] = "1"
import warnings
warnings.filterwarnings("ignore")

from nicto_neural.brain_inference import BrainInferenceEngine
engine = BrainInferenceEngine()


class NiktoAPIHandler(BaseHTTPRequestHandler):
    start_time = time.time()

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self._send_json({})

    def do_GET(self):
        if self.path == "/status":
            self._send_json(self._get_status())
        elif self.path == "/health":
            self._send_json({"status": "ok", "uptime": time.time() - self.start_time})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            data = json.loads(body)
            response = self._handle_chat(data.get("message", ""))
            self._send_json({"response": response})
        else:
            self._send_json({"error": "not found"}, 404)

    def _get_status(self) -> dict:
        s = engine.get_status()
        return {
            **s,
            "platform": sys.platform,
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
            "memory_gb": self._get_memory(),
            "uptime_hours": (time.time() - self.start_time) / 3600,
            "active_skills": 100,
            "knowledge_bases": 17,
        }

    def _handle_chat(self, message: str) -> str:
        if not message:
            return "Silence is golden. Speak, and I shall create."
        return engine.chat(message)

    @staticmethod
    def _try_import(module: str) -> bool:
        try:
            __import__(module)
            return True
        except ImportError:
            return False

    @staticmethod
    def _check_cuda() -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    @staticmethod
    def _get_memory() -> float:
        try:
            import psutil
            return round(psutil.virtual_memory().total / (1024**3), 1)
        except ImportError:
            return 16.0

    @staticmethod
    def _load_cycles() -> int:
        try:
            ckpt = os.path.join(PROJECT_ROOT, "nicto_neural", "checkpoints", "superior_creative_state.json")
            if os.path.exists(ckpt):
                with open(ckpt) as f:
                    state = json.load(f)
                    return len(state.get("history", {}).get("cycles", []))
            return 2
        except Exception:
            return 2

    def log_message(self, format, *args):
        sys.stderr.write(f"[NICTO API] {args[0]}\n")


def main():
    port = int(os.environ.get("NIKTO_PORT", 8765))
    print(f"\n  {'='*56}")
    print(f"  NICTO Desktop API Server")
    print(f"  {'='*56}")
    print(f"  Architecture: 7-Brain MoE+MLA (19 heads, 70 subnetworks)")
    print(f"  Listening on: http://127.0.0.1:{port}")
    print(f"  Endpoints:")
    print(f"    GET  /status  - System status")
    print(f"    GET  /health  - Health check")
    print(f"    POST /chat    - Chat with NICTO")
    print(f"  {'='*56}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down NICTO server...")
        server.server_close()


if __name__ == "__main__":
    main()
