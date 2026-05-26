import sys
import os

# Re-export the nikto API app which has all 24+ endpoints wired to NiktoBrain
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "nikto-core", "src"))
from nikto.api.routes import app, ChatRequest

# Add kyros-specific compatibility endpoints
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


@app.get("/memory/search")
async def memory_search(q: str = ""):
    from nikto.brain.core import NiktoBrain
    b = NiktoBrain()
    await b.awaken(restore=True)
    results = b.recall_memories(q, 3)
    await b.sleep()
    return {"results": [{"content": str(r)[:200]} for r in results]}


@app.get("/")
async def root():
    return {"name": "KYROS", "version": "0.2.0", "service": "kyros"}
