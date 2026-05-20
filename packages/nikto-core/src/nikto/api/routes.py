import logging
import platform
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logger = logging.getLogger(__name__)

_agent = None
_orch = None
_miner = None

WEBUI_DIR = Path(__file__).parent.parent / "webui"


def _ensure_agent():
    global _agent
    if _agent is not None:
        return True
    try:
        from nikto.agent.base import Agent
        from nikto.config.settings import NiktoConfig
        import tempfile
        td = tempfile.mkdtemp()
        from nikto.config.settings import ModelConfig
        cfg = NiktoConfig(data_dir=td, model=ModelConfig(provider="local", model="local"))
        _agent = Agent(config=cfg)
        logger.info("Agent auto-initialized")
        return True
    except Exception as e:
        logger.warning(f"Agent auto-init failed: {e}")
        return False


app = FastAPI(title="NIKTO API", version="1.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    mode: str = "build"


class ChatResponse(BaseModel):
    response: str
    mode: str


class TicketCreate(BaseModel):
    title: str
    description: str = ""
    priority: str = "MEDIUM"


class AgentRegister(BaseModel):
    name: str
    role: str = "worker"
    skills: list = []


def set_globals(agent=None, orch=None, miner=None):
    global _agent, _orch, _miner
    if agent:
        _agent = agent
    if orch:
        _orch = orch
    if miner:
        _miner = miner


@app.get("/")
async def root():
    return {"name": "NIKTO", "version": "1.0.0", "platform": platform.system(), "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok", "agent_ready": _agent is not None}


@app.get("/chat-ui")
async def chat_ui():
    html_path = WEBUI_DIR / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>NIKTO Chat</h1><p>Web UI not found. Run install.py first.</p>")


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not _ensure_agent():
        raise HTTPException(503, "Agent failed to initialize")
    resp = await _agent.run_sync(req.message)
    return ChatResponse(response=resp, mode=req.mode)


@app.get("/memory/search")
async def memory_search(q: str = "", limit: int = 10):
    from nikto.config.settings import MemoryConfig
    from nikto.memory.base import MemorySystem
    mem = MemorySystem(MemoryConfig())
    if q:
        results = mem.search(q, limit=limit)
    else:
        results = mem.recent(limit=limit)
    return {"results": results}


@app.post("/memory/store")
async def memory_store(key: str, value: str):
    from nikto.config.settings import MemoryConfig
    from nikto.memory.base import MemorySystem
    mem = MemorySystem(MemoryConfig())
    mem.store(key, value, {"source": "api"})
    return {"stored": key}


@app.get("/system/info")
async def system_info():
    import psutil
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_free_gb": psutil.disk_usage("/").free / 1e9,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
    }


@app.get("/sources/summary")
async def sources_summary():
    if not _ensure_agent():
        raise HTTPException(503, "Agent not initialized")
    return {"sources": _agent.sourcing.get_session_summary()}


@app.post("/sources/clear")
async def sources_clear():
    if not _ensure_agent():
        raise HTTPException(503, "Agent not initialized")
    _agent.sourcing.clear_session()
    return {"status": "cleared"}


@app.get("/voice/profiles")
async def voice_profiles():
    if not _ensure_agent():
        raise HTTPException(503, "Agent not initialized")
    return {"profiles": _agent.voice.list_profiles()}


@app.post("/voice/set-profile")
async def voice_set_profile(name: str = "default"):
    if not _ensure_agent():
        raise HTTPException(503, "Agent not initialized")
    _agent.voice.set_profile(name)
    return {"profile": name}


@app.get("/evolution/status")
async def evolution_status():
    if not _ensure_agent():
        raise HTTPException(503, "Agent not initialized")
    return {
        "level": _agent.evolution.level,
        "xp": _agent.evolution.xp,
        "skills": list(_agent.evolution.skills),
    }


@app.get("/infinite/status")
async def infinite_status():
    if not _ensure_agent():
        raise HTTPException(503, "Agent not initialized")
    return {"total_processed": _agent.infinite_context.total_processed}
