"""NIKTO Core — CLI entry point for uvicorn."""
import sys, os
os.environ["NIKTO_NO_AUTH"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import uvicorn
from nikto.server import app
if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
