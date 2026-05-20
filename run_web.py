#!/usr/bin/env python3
"""NIKTO Web Server — Launch the web UI and API."""
import uvicorn

if __name__ == "__main__":
    print("=" * 56)
    print("  NIKTO WEB SERVER — http://localhost:8000")
    print("  Chat UI: http://localhost:8000/chat-ui")
    print("  API Docs: http://localhost:8000/docs")
    print("=" * 56)
    uvicorn.run("nikto.api.routes:app", host="0.0.0.0", port=8000, reload=True)
