import asyncio
import os
import platform
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from nikto.brain.core import NiktoBrain
from nikto.brain.models import ThinkingStyle


brain: NiktoBrain = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global brain
    brain = NiktoBrain()
    await brain.awaken(restore=True)
    yield
    await brain.sleep()


app = FastAPI(title="NIKTO API", version="0.3.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    mode: str = "analytical"
    context: Optional[dict] = None


class BusinessPlanRequest(BaseModel):
    model_name: Optional[str] = None
    skills: list[str] = ["python", "security"]
    location: str = "Nairobi, Kenya"
    hours_per_week: int = 20


class EagleAnalyzeRequest(BaseModel):
    target: str
    depth: str = "deep"


class PredictionRequest(BaseModel):
    question: str
    timeframe: str = "30_day"
    domain: Optional[str] = None


class VerifyPredictionRequest(BaseModel):
    prediction_id: str
    actual_outcome: str


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "0.3.0",
        "service": "nikto",
        "brain_awake": brain.is_awake if brain else False,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/system/info")
async def system_info():
    try:
        import psutil as psutil_module
        cpu = psutil_module.cpu_percent(interval=0.1)
        mem = psutil_module.virtual_memory().percent
    except Exception:
        cpu = 0
        mem = 0
    return {
        "cpu_percent": cpu,
        "memory_percent": mem,
        "platform": platform.system(),
        "platform_release": platform.release(),
        "hostname": platform.node(),
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    ctx = {}
    if req.mode:
        ctx["thinking_style"] = req.mode
    if req.context:
        ctx.update(req.context)
    result = brain.process(req.message, ctx)
    return {
        "response": result["response"],
        "thought": result["thought"]["content"][:200],
        "emotional_state": result["emotional_state"],
        "confidence": result["thought"]["confidence"],
    }


@app.get("/brain/status")
async def brain_status():
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    return brain.get_status()


@app.get("/brain/introspect")
async def brain_introspect():
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    return brain.introspect()


@app.post("/brain/save")
async def brain_save():
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    p = brain.save_state()
    return {"saved": True, "path": p}


@app.get("/autopilot/status")
async def autopilot_status():
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    return brain.autopilot_pro.get_status()


@app.post("/autopilot/start")
async def autopilot_start():
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    await brain.autopilot_pro.start()
    return {"running": True}


@app.post("/autopilot/stop")
async def autopilot_stop():
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    report = await brain.autopilot_pro.stop()
    return report.to_dict()


@app.get("/autopilot/report")
async def autopilot_report():
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    report = await brain.autopilot_pro.generate_full_report()
    return report.to_dict()


@app.get("/business/models")
async def business_models():
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    models = await brain.zero_capital.list_models()
    return {"models": models}


@app.post("/business/plan")
async def business_plan(req: BusinessPlanRequest):
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    plan = await brain.zero_capital.start_business(
        req.model_name, req.skills, req.location, req.hours_per_week
    )
    return plan.to_dict()


@app.get("/eagle/status")
async def eagle_status():
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    return brain.eagle_eye.get_status()


@app.post("/eagle/analyze")
async def eagle_analyze(req: EagleAnalyzeRequest):
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    analysis = await brain.eagle_eye.analyze_target(req.target, req.depth)
    return analysis.to_dict()


@app.post("/eagle/open")
async def eagle_open():
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    await brain.eagle_eye.open()
    return {"watching": True}


@app.post("/eagle/close")
async def eagle_close():
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    report = await brain.eagle_eye.close()
    return report.to_dict()


@app.get("/predict/status")
async def predict_status():
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    return brain.future_engine.get_status()


@app.post("/predict")
async def predict(req: PredictionRequest):
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    prediction = await brain.future_engine.predict(req.question, req.timeframe, req.domain)
    return prediction.to_dict()


@app.post("/predict/verify")
async def predict_verify(req: VerifyPredictionRequest):
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    result = await brain.future_engine.verify_prediction(req.prediction_id, req.actual_outcome)
    return result.to_dict()


@app.get("/predict/accuracy")
async def predict_accuracy():
    if not brain:
        raise HTTPException(503, "Brain not initialized")
    report = await brain.future_engine.get_accuracy_report()
    return report


@app.get("/model/status")
async def model_status():
    try:
        from kyros.model_manager import ModelManager
        mm = ModelManager()
        installed = mm.list_installed()
        tier = mm.detect_hardware_tier()
        rec = mm.recommend_model()
        return {
            "tier": tier,
            "installed": installed,
            "recommended": rec["model"]["name"],
            "models_dir": str(mm.models_dir),
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


@app.post("/model/download")
async def model_download(tier: str = "tier1"):
    try:
        from kyros.model_manager import ModelManager
        mm = ModelManager()
        result = mm.download_model(tier)
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/status")
async def status():
    if not brain:
        return {"status": "initializing"}
    return {
        "status": "running",
        "version": "0.3.0",
        "brain_awake": brain.is_awake,
        "cycles": brain.cycle_count,
        "thoughts": len(brain.reasoner.thought_history),
        "memories": len(brain.memory.fragments),
        "goals": len(brain.goals.goals),
    }
