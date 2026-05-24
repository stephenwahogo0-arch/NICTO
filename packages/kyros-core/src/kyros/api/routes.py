from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Kyros API", version="0.2.0")


class ChatRequest(BaseModel):
    message: str
    provider: str = "local"
    stream: bool = False


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0", "service": "kyros"}


@app.post("/chat")
async def chat(req: ChatRequest):
    return {"response": f"Received: {req.message}", "provider": req.provider, "mode": "api"}


@app.get("/status")
async def status():
    return {"status": "running", "version": "0.2.0", "providers": ["anthropic", "openai", "gemini", "deepseek", "local"], "mode": "online"}
