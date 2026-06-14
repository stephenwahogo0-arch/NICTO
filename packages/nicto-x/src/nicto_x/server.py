"""Nicto X API Server — Full-featured FastAPI with neural core, agents, memory, research, code gen, and benchmarks."""

import os
import json
import time
import asyncio
import logging
from typing import Optional
from datetime import datetime

try:
    from fastapi import FastAPI, HTTPException, Depends, Header, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
except ImportError:
    raise ImportError("FastAPI not installed. Run: pip install fastapi uvicorn")

from nicto_x import NictoXOrchestrator, AgentBus
from nicto_x.core.config import NictoXConfig

logger = logging.getLogger("nicto_x.server")

app = FastAPI(title="Nicto X API", version="0.2.0", docs_url="/docs")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

orchestrator: Optional[NictoXOrchestrator] = None
require_auth: bool = True
request_count = 0
start_time = time.time()


class AgentRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=32000)
    mode: Optional[str] = "auto"


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32000)
    conversation_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32000)
    correction: str = Field(..., min_length=1, max_length=32000)
    model_id: Optional[str] = None


class CodeGenRequest(BaseModel):
    spec: str = Field(..., min_length=1, max_length=32000)
    language: str = Field(default="python", max_length=32)


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=2000)


class NeuralRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=32000)


class KnowledgeQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=10, ge=1, le=100)


ALLOWED_TOKENS: set = set()


def load_tokens():
    token_file = os.path.expanduser("~/.nikto/nicto_x_tokens.json")
    try:
        if os.path.exists(token_file):
            with open(token_file) as f:
                data = json.load(f)
                ALLOWED_TOKENS.update(data.get("tokens", []))
    except Exception as e:
        logger.warning(f"Failed to load tokens: {e}")


def save_token(token: str):
    ALLOWED_TOKENS.add(token)
    token_file = os.path.expanduser("~/.nikto/nicto_x_tokens.json")
    os.makedirs(os.path.dirname(token_file), exist_ok=True)
    try:
        existing = []
        if os.path.exists(token_file):
            with open(token_file) as f:
                existing = json.load(f).get("tokens", [])
        if token not in existing:
            existing.append(token)
        with open(token_file, "w") as f:
            json.dump({"tokens": existing}, f)
    except Exception as e:
        logger.warning(f"Failed to save token: {e}")


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    if not require_auth:
        return None
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required (X-API-Key header)")
    if x_api_key not in ALLOWED_TOKENS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


@app.on_event("startup")
async def startup():
    global orchestrator
    logger.info("Initializing Nicto X orchestrator...")
    load_tokens()
    if not ALLOWED_TOKENS:
        import hashlib, secrets
        default_token = f"nx-{secrets.token_hex(24)}"
        save_token(default_token)
        logger.info(f"Generated default Nicto X token: {default_token}")

    config = NictoXConfig(version="0.2.0")
    orchestrator = NictoXOrchestrator(config)
    await orchestrator.start()
    logger.info("Nicto X orchestrator ready.")


@app.on_event("shutdown")
async def shutdown():
    global orchestrator
    if orchestrator:
        await orchestrator.stop()
        logger.info("Nicto X orchestrator stopped.")


@app.get("/health")
async def health():
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    status = orchestrator.get_status()
    return {
        "status": "ok",
        "version": "0.2.0",
        "orchestrator_ready": True,
        "agents_available": status.get("agents", []),
        "neural_core": status.get("neural_core", {}),
        "uptime": time.time(),
        "model": "nicto_x",
    }


@app.post("/chat")
async def chat(req: ChatRequest, api_key: Optional[str] = Depends(verify_api_key)):
    global request_count
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    request_count += 1
    start = time.time()
    context = {"conversation_id": req.conversation_id} if req.conversation_id else {}
    try:
        result = await orchestrator.process(req.message, context=context)
    except Exception as e:
        logger.error(f"Process failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    elapsed = (time.time() - start) * 1000
    return {"response": result.get("response", ""), "conversation_id": result.get("conversation_id"), "model": "nicto_x", "latency_ms": round(elapsed, 2), "confidence": result.get("confidence"), "agents_used": result.get("agents_used", []), "neural_processing": result.get("neural_processing")}


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest, api_key: Optional[str] = Depends(verify_api_key)):
    global request_count
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    request_count += 1
    context = {"conversation_id": req.conversation_id} if req.conversation_id else {}
    try:
        result = await orchestrator.process(req.message, context=context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    response_text = result.get("response", "")

    async def event_stream():
        words = response_text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            data = json.dumps({"choices": [{"delta": {"content": chunk}}]})
            yield f"data: {data}\n\n"
            await asyncio.sleep(0.02)
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/agent/run")
async def run_agent(req: AgentRequest, api_key: Optional[str] = Depends(verify_api_key)):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    start = time.time()
    try:
        result = await orchestrator.execute_task(req.task, {"mode": req.mode})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    elapsed = (time.time() - start) * 1000
    return {"task": req.task, "result": result.get("output", result.get("response", str(result))), "plan": result.get("plan", []), "latency_ms": round(elapsed, 2)}


@app.get("/agents")
async def list_agents(api_key: Optional[str] = Depends(verify_api_key)):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    agents = orchestrator.agents if hasattr(orchestrator, 'agents') else {}
    return {"agents": [{"name": name, "status": "ready", "type": type(agent).__name__} for name, agent in agents.items()]}


@app.get("/metrics")
async def get_metrics(api_key: Optional[str] = Depends(verify_api_key)):
    global request_count
    uptime = time.time() - start_time
    status = orchestrator.get_status() if orchestrator else {}
    return {"uptime_seconds": uptime, "request_count": request_count, "agents_loaded": len(status.get("agents", [])), "model": "nicto_x_v2", "memory": orchestrator.get_memory_status() if orchestrator else {}, "neural": status.get("neural_core", {}), "distributed": status.get("distributed", {})}


@app.get("/memory")
async def get_memory(api_key: Optional[str] = Depends(verify_api_key)):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return orchestrator.get_memory_status()


@app.post("/neural/process")
async def neural_process(req: NeuralRequest, api_key: Optional[str] = Depends(verify_api_key)):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    result = await orchestrator.process_neural(req.text)
    return result


@app.get("/neural/info")
async def neural_info(api_key: Optional[str] = Depends(verify_api_key)):
    if not orchestrator or not hasattr(orchestrator, 'neural_core'):
        raise HTTPException(status_code=503, detail="Neural core unavailable")
    return orchestrator.neural_core.get_info()


@app.post("/code/generate")
async def code_generate(req: CodeGenRequest, api_key: Optional[str] = Depends(verify_api_key)):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    result = await orchestrator.generate_code(req.spec, req.language)
    return result


@app.post("/research/search")
async def research_search(req: ResearchRequest, api_key: Optional[str] = Depends(verify_api_key)):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    result = await orchestrator.research_topic(req.topic)
    return result


@app.post("/research/hypothesis")
async def research_hypothesis(req: ResearchRequest, api_key: Optional[str] = Depends(verify_api_key)):
    if not orchestrator or not hasattr(orchestrator, 'research'):
        raise HTTPException(status_code=503, detail="Research unavailable")
    hyp = await orchestrator.research.generate_hypothesis(req.topic)
    return hyp


@app.post("/knowledge/search")
async def knowledge_search(req: KnowledgeQuery, api_key: Optional[str] = Depends(verify_api_key)):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    result = await orchestrator.search_knowledge(req.query, req.top_k)
    return result


@app.get("/benchmarks")
async def get_benchmarks(api_key: Optional[str] = Depends(verify_api_key)):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return orchestrator.get_benchmark_status()


@app.post("/benchmarks/run")
async def run_benchmarks(api_key: Optional[str] = Depends(verify_api_key)):
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    results = await orchestrator.run_benchmarks()
    return {"results": results}


@app.post("/distributed/submit")
async def distributed_submit(req: AgentRequest, api_key: Optional[str] = Depends(verify_api_key)):
    if not orchestrator or not hasattr(orchestrator, 'distributed_executor'):
        raise HTTPException(status_code=503, detail="Distributed executor unavailable")
    task_id = await orchestrator.distributed_executor.submit(req.task, {"task": req.task}, 5)
    return {"task_id": task_id, "status": "submitted"}


@app.get("/distributed/status")
async def distributed_status(api_key: Optional[str] = Depends(verify_api_key)):
    if not orchestrator or not hasattr(orchestrator, 'distributed_executor'):
        raise HTTPException(status_code=503, detail="Distributed executor unavailable")
    return orchestrator.distributed_executor.get_status()


@app.post("/feedback")
async def submit_feedback(req: FeedbackRequest, api_key: Optional[str] = Depends(verify_api_key)):
    feedback_dir = os.path.expanduser("~/.nikto/feedback")
    os.makedirs(feedback_dir, exist_ok=True)
    entry = {"id": f"nx-fb-{int(time.time())}", "timestamp": datetime.utcnow().isoformat(), "message": req.message, "correction": req.correction, "model_id": req.model_id or "nicto_x_v2", "applied": False}
    with open(os.path.join(feedback_dir, "nicto_x_feedback.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")
    return {"success": True, "feedback_id": entry["id"]}


def serve(host: str = "127.0.0.1", port: int = 8000, no_auth: bool = False):
    global require_auth
    require_auth = not no_auth
    import uvicorn
    logger.info(f"Starting Nicto X API v0.2.0 on {host}:{port} (auth={'required' if require_auth else 'disabled'})")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    serve()
