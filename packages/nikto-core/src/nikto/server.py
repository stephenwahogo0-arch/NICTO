"""Nikto API Server — bridges desktop/mobile frontends to the Nikto brain."""

import os
import json
import time
import asyncio
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime

try:
    from fastapi import FastAPI, HTTPException, Depends, Header, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
except ImportError:
    raise ImportError(
        "FastAPI dependencies not installed. Run: pip install fastapi uvicorn"
    )

from nikto.brain.core import NiktoBrain
from nikto.config.api_keys import NiktoKeyManager

logger = logging.getLogger("nikto.server")

MODEL_PIPELINES = {
    "nicto_kyros": "kyros",
    "nicto_omega": "omega",
    "nicto_main": "main",
    "nicto_x": "x",
}

app = FastAPI(title="Nikto API", version="0.3.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

brain: Optional[NiktoBrain] = None
key_manager: Optional[NiktoKeyManager] = None
require_auth: bool = os.environ.get("NIKTO_NO_AUTH") != "1"
feedback_store: list[dict] = []
metrics_store: dict = {
    "start_time": time.time(),
    "request_count": 0,
    "total_latency_ms": 0.0,
    "latency_samples": [],
}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32000)
    conversation_id: Optional[str] = None
    model_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None
    thinking_style: Optional[str] = None


class FeedbackRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32000)
    correction: str = Field(..., min_length=1, max_length=32000)
    model_id: Optional[str] = None


class MetricRecordRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    value: float = Field(...)
    category: str = Field(default="custom", max_length=64)
    tags: Optional[dict] = None


class GameBuildRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=32000)


class GameCreateRequest(BaseModel):
    name: str = Field(default="NICTO_Game", max_length=128)
    genre: str = Field(default="fps", max_length=64)
    width: int = Field(default=64, ge=8, le=1024)
    height: int = Field(default=64, ge=8, le=1024)
    enemies: int = Field(default=10, ge=0, le=500)
    npcs: int = Field(default=5, ge=0, le=500)
    description: str = Field(default="", max_length=2000)


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    if not require_auth:
        return None
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required (X-API-Key header)")
    if not key_manager or not key_manager.validate_key(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid or revoked API key")
    return x_api_key


def process_with_model(input_text: str, context: dict, model_id: str = "nicto_omega") -> dict:
    pipeline = MODEL_PIPELINES.get(model_id, "omega")
    if pipeline == "kyros":
        return brain.process_kyros(input_text, context)
    elif pipeline == "main":
        return brain.process_main(input_text, context)
    elif pipeline == "x":
        return brain.process_x(input_text, context)
    return brain.process(input_text, context)


@app.on_event("startup")
async def startup():
    global brain, key_manager
    logger.info("Initializing Nikto brain...")
    brain = NiktoBrain()
    await brain.awaken(restore=True)
    key_manager = brain.api_keys if hasattr(brain, 'api_keys') else NiktoKeyManager()
    logger.info("Nikto brain is awake and ready.")


@app.on_event("shutdown")
async def shutdown():
    global brain
    if brain:
        await brain.sleep(persist=True)
        logger.info("Nikto brain saved and asleep.")


@app.get("/health")
async def health(x_model_id: Optional[str] = Header(None)):
    if not brain:
        raise HTTPException(status_code=503, detail="Brain not initialized")
    status = brain.get_status()
    model_id = x_model_id or "nicto_omega"
    return {
        "status": "ok",
        "version": "0.3.0",
        "brain_active": brain.is_awake,
        "cycle_count": status.get("cycle", 0),
        "uptime": time.time(),
        "model": model_id,
        "available_models": list(MODEL_PIPELINES.keys()),
    }


@app.get("/models")
async def list_models():
    return {
        "models": [
            {"id": "nicto_kyros", "name": "Nicto Kyros", "description": "Lightning-fast minimal brain — identity + basic memory + direct response", "version": "0.1.0", "capabilities": ["Chat", "Memory", "Identity"]},
            {"id": "nicto_omega", "name": "Nicto Omega", "description": "Core reasoning engine — deep chain-of-thought, memory consolidation, ethical deliberation", "version": "0.2.0", "capabilities": ["Reasoning", "Memory", "Learning", "Emotional Core", "Conscience", "Metacognition", "Dream Steerer", "Truth Engine"]},
            {"id": "nicto_main", "name": "Nicto Main", "description": "Full-featured brain — Omega + security scanning, enhanced reasoning, autopilot suggestions", "version": "0.3.0", "capabilities": ["Reasoning", "Memory", "Learning", "Emotional Core", "Conscience", "Security Scanning", "Metacognition", "Dream Steerer", "Truth Engine", "Autopilot", "Performance Graph"]},
            {"id": "nicto_x", "name": "Nicto X", "description": "Frontier agent system — multi-agent orchestration, planning, coding, research, distributed execution", "version": "1.0.0", "capabilities": ["Research", "Coding", "Planning", "Evaluation", "Memory Agent", "Vision Agent", "Security Agent", "Agent Swarming", "Distributed Execution", "Self-Improvement", "Knowledge Graph", "Scientific Research"]},
        ]
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    api_key: Optional[str] = Depends(verify_api_key),
    x_model_id: Optional[str] = Header(None),
):
    if not brain:
        raise HTTPException(status_code=503, detail="Brain not initialized")

    model_id = req.model_id or x_model_id or "nicto_omega"
    context = {}
    if api_key:
        context["api_key"] = api_key
    if req.conversation_id:
        context["conversation_id"] = req.conversation_id

    start = time.time()
    try:
        result = process_with_model(input_text=req.message, context=context, model_id=model_id)
    finally:
        elapsed = (time.time() - start) * 1000
        metrics_store["request_count"] += 1
        metrics_store["total_latency_ms"] += elapsed
        metrics_store["latency_samples"].append(elapsed)
        if len(metrics_store["latency_samples"]) > 1000:
            metrics_store["latency_samples"] = metrics_store["latency_samples"][-1000:]

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return ChatResponse(
        response=result.get("response", ""),
        conversation_id=result.get("memory_id"),
        thinking_style=result.get("thought", {}).get("style"),
    )


@app.post("/chat/stream")
async def chat_stream(
    req: ChatRequest,
    api_key: Optional[str] = Depends(verify_api_key),
    x_model_id: Optional[str] = Header(None),
):
    if not brain:
        raise HTTPException(status_code=503, detail="Brain not initialized")

    model_id = req.model_id or x_model_id or "nicto_omega"
    context = {}
    if api_key:
        context["api_key"] = api_key
    if req.conversation_id:
        context["conversation_id"] = req.conversation_id

    start = time.time()
    try:
        result = process_with_model(input_text=req.message, context=context, model_id=model_id)
    finally:
        elapsed = (time.time() - start) * 1000
        metrics_store["request_count"] += 1
        metrics_store["total_latency_ms"] += elapsed
        metrics_store["latency_samples"].append(elapsed)

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


@app.get("/metrics")
async def get_metrics(api_key: Optional[str] = Depends(verify_api_key)):
    if not brain:
        raise HTTPException(status_code=503, detail="Brain not initialized")
    brain_status = brain.get_status()
    uptime = time.time() - metrics_store["start_time"]
    avg_latency = (
        metrics_store["total_latency_ms"] / metrics_store["request_count"]
        if metrics_store["request_count"] > 0
        else 0
    )

    return {
        "uptime_seconds": uptime,
        "request_count": metrics_store["request_count"],
        "average_latency_ms": round(avg_latency, 2),
        "brain": brain_status,
        "memory": brain.memory.summarize() if hasattr(brain, 'memory') else {},
        "learning": brain.learner.export() if hasattr(brain, 'learner') else {},
        "performance": brain.performance.summary_report() if hasattr(brain, 'performance') else {},
        "truth": brain.truth.get_stats() if hasattr(brain, 'truth') else {},
        "meta_cognition": {
            "total_observations": len(brain.meta_cognition.observation_history) if hasattr(brain, 'meta_cognition') else 0,
        },
    }


@app.get("/metrics/performance")
async def get_performance_metrics(api_key: Optional[str] = Depends(verify_api_key)):
    if not brain or not hasattr(brain, 'performance'):
        raise HTTPException(status_code=503, detail="Performance graph unavailable")
    return brain.performance.summary_report()


@app.get("/metrics/performance/{name}")
async def get_metric_by_name(
    name: str,
    api_key: Optional[str] = Depends(verify_api_key),
):
    if not brain or not hasattr(brain, 'performance'):
        raise HTTPException(status_code=503, detail="Performance graph unavailable")
    metric = brain.performance.get_metric(name)
    if not metric:
        raise HTTPException(status_code=404, detail=f"Metric '{name}' not found")
    return metric


@app.get("/metrics/performance/{name}/history")
async def get_metric_history(
    name: str,
    n: int = Query(default=50, le=500),
    api_key: Optional[str] = Depends(verify_api_key),
):
    if not brain or not hasattr(brain, 'performance'):
        raise HTTPException(status_code=503, detail="Performance graph unavailable")
    values = brain.performance.get_latest_values(name, n=n)
    return {"name": name, "values": values}


@app.post("/metrics/record")
async def record_metric(
    req: MetricRecordRequest,
    api_key: Optional[str] = Depends(verify_api_key),
):
    if not brain or not hasattr(brain, 'performance'):
        raise HTTPException(status_code=503, detail="Performance graph unavailable")
    brain.performance.record(req.name, req.value, req.category, tags=req.tags)
    return {"success": True, "name": req.name, "value": req.value}


@app.get("/training/history")
async def get_training_history(api_key: Optional[str] = Depends(verify_api_key)):
    if not brain:
        raise HTTPException(status_code=503, detail="Brain not initialized")
    learner_data = brain.learner.export() if hasattr(brain, 'learner') else {}
    return {"entries": [], "skills": learner_data.get("skills", {}), "total_lessons": learner_data.get("total_lessons", 0)}


@app.get("/training/skills")
async def get_training_skills(api_key: Optional[str] = Depends(verify_api_key)):
    if not brain or not hasattr(brain, 'learner'):
        raise HTTPException(status_code=503, detail="Learner unavailable")
    return {"skills": brain.learner.skill_progress}


@app.get("/training/lessons")
async def get_training_lessons(api_key: Optional[str] = Depends(verify_api_key)):
    if not brain or not hasattr(brain, 'learner'):
        raise HTTPException(status_code=503, detail="Learner unavailable")
    return {"lessons": list(brain.learner.lesson_store.values())}


@app.get("/training/mastery/{topic}")
async def get_topic_mastery(
    topic: str,
    api_key: Optional[str] = Depends(verify_api_key),
):
    if not brain or not hasattr(brain, 'learner'):
        raise HTTPException(status_code=503, detail="Learner unavailable")
    score = brain.learner.get_mastery(topic)
    level = brain.learner.get_level(topic)
    return {"topic": topic, "mastery_score": score, "level": level.value if hasattr(level, 'value') else str(level)}


@app.post("/feedback")
async def submit_feedback(
    req: FeedbackRequest,
    api_key: Optional[str] = Depends(verify_api_key),
):
    if not brain:
        raise HTTPException(status_code=503, detail="Brain not initialized")

    entry = {
        "id": f"fb-{int(time.time())}-{len(feedback_store)}",
        "timestamp": datetime.utcnow().isoformat(),
        "message": req.message,
        "correction": req.correction,
        "model_id": req.model_id or "nicto_omega",
        "applied": False,
    }
    feedback_store.append(entry)

    feedback_dir = Path.home() / ".nikto" / "feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)
    feedback_file = feedback_dir / "feedback_log.jsonl"
    with open(feedback_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    try:
        if hasattr(brain, 'learner'):
            brain.learner.learn(
                topic="user_feedback",
                content=f"User correction: {req.correction[:200]}",
                source="feedback_api",
            )
    except Exception as e:
        logger.warning(f"Failed to register feedback as lesson: {e}")

    return {"success": True, "feedback_id": entry["id"]}


@app.get("/feedback")
async def list_feedback(
    limit: int = Query(default=50, le=500),
    api_key: Optional[str] = Depends(verify_api_key),
):
    return {"feedback": feedback_store[-limit:]}


@app.get("/conversations")
async def list_conversations(api_key: Optional[str] = Depends(verify_api_key)):
    if not brain:
        raise HTTPException(status_code=503, detail="Brain not initialized")
    memories = brain.recall_memories(query="", top_k=50) if hasattr(brain, 'recall_memories') else []
    convs = []
    for m in memories:
        if hasattr(m, 'id') and hasattr(m, 'content'):
            convs.append({
                "id": str(m.id),
                "title": (m.content or "")[:60],
                "updated_at": str(getattr(m, 'timestamp', '')),
            })
    return convs


@app.get("/api-keys")
async def list_api_keys(api_key: Optional[str] = Depends(verify_api_key)):
    if not key_manager:
        raise HTTPException(status_code=503, detail="Key manager not initialized")
    return key_manager.list_keys()


@app.post("/game/build")
async def game_build(
    req: GameBuildRequest,
    api_key: Optional[str] = Depends(verify_api_key),
):
    if not brain:
        raise HTTPException(status_code=503, detail="Brain not initialized")
    if not hasattr(brain, 'game_engine'):
        raise HTTPException(status_code=503, detail="Game engine unavailable")
    result = await brain.build_game_from_prompt(req.prompt)
    return result


@app.post("/game/create")
async def game_create(
    req: GameCreateRequest,
    api_key: Optional[str] = Depends(verify_api_key),
):
    if not brain:
        raise HTTPException(status_code=503, detail="Brain not initialized")
    if not hasattr(brain, 'game_engine'):
        raise HTTPException(status_code=503, detail="Game engine unavailable")
    result = await brain.create_game(
        name=req.name,
        genre=req.genre,
        width=req.width,
        height=req.height,
        enemies=req.enemies,
        npcs=req.npcs,
        description=req.description,
    )
    return result


@app.get("/game/status")
async def game_status(api_key: Optional[str] = Depends(verify_api_key)):
    if not brain:
        raise HTTPException(status_code=503, detail="Brain not initialized")
    if not hasattr(brain, 'game_engine'):
        raise HTTPException(status_code=503, detail="Game engine unavailable")
    status = await brain.get_game_status()
    return status


@app.get("/game/list")
async def game_list(api_key: Optional[str] = Depends(verify_api_key)):
    if not brain:
        raise HTTPException(status_code=503, detail="Brain not initialized")
    if not hasattr(brain, 'game_engine'):
        raise HTTPException(status_code=503, detail="Game engine unavailable")
    games = await brain.list_generated_games()
    return {"games": games, "count": len(games)}


@app.get("/game/{name}")
async def game_get(
    name: str,
    api_key: Optional[str] = Depends(verify_api_key),
):
    if not brain:
        raise HTTPException(status_code=503, detail="Brain not initialized")
    if not hasattr(brain, 'game_engine'):
        raise HTTPException(status_code=503, detail="Game engine unavailable")
    game = await brain.get_game_by_name(name)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game '{name}' not found")
    return game


@app.delete("/game/{name}")
async def game_delete(
    name: str,
    api_key: Optional[str] = Depends(verify_api_key),
):
    if not brain:
        raise HTTPException(status_code=503, detail="Brain not initialized")
    if not hasattr(brain, 'game_engine'):
        raise HTTPException(status_code=503, detail="Game engine unavailable")
    ok = await brain.delete_game(name)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Game '{name}' not found")
    return {"success": True, "deleted": name}


def serve(host: str = "127.0.0.1", port: int = 5000, no_auth: bool = False):
    global require_auth
    require_auth = not no_auth

    import uvicorn
    logger.info(f"Starting Nikto API server on {host}:{port} (auth={'required' if require_auth else 'disabled'})")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    import sys
    port = 5000
    no_auth = False
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--port" and i + 2 < len(sys.argv):
            port = int(sys.argv[i + 2])
        elif arg == "--no-auth":
            no_auth = True
    serve(port=port, no_auth=no_auth)
