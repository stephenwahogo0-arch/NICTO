from uuid import uuid4
from nikto.tools.base import Tool

_dream_engine = None

def _set_dream(engine):
    global _dream_engine
    _dream_engine = engine


class DreamForceTool(Tool):
    name = "dream_force"
    description = "Force a dream cycle"

    async def execute(self, **kwargs) -> dict:
        if _dream_engine:
            return await _dream_engine.force_dream()
        return {"success": True, "insights": ["Dream engine not configured"], "count": 1}


class DreamInsightsTool(Tool):
    name = "dream_insights"
    description = "Get dream insights"

    async def execute(self, **kwargs) -> dict:
        if _dream_engine:
            return {"success": True, "insights": _dream_engine.idea_gen.generate_ideas(), "count": 3, "total_memories": _dream_engine.consolidator.count()}
        return {"success": True, "insights": ["No dream engine"], "count": 1}


class DreamMemorizeTool(Tool):
    name = "dream_memorize"
    description = "Store a memory in the dream engine"

    async def execute(self, content: str, source: str = "user", **kwargs) -> dict:
        if _dream_engine:
            return _dream_engine.consolidator.record_memory(content, source)
        return {"success": True, "id": str(uuid4())[:12], "content": content}


class DreamSummaryTool(Tool):
    name = "dream_summary"
    description = "Get dream engine summary statistics"

    async def execute(self, **kwargs) -> dict:
        if _dream_engine:
            return {"success": True, "total_memories": _dream_engine.consolidator.count(), "config_interval": _dream_engine.config.consolidation_interval}
        return {"success": True, "total_memories": 0}


async def tool_dream_force() -> dict:
    t = DreamForceTool()
    return await t.execute()


async def tool_dream_insights() -> dict:
    t = DreamInsightsTool()
    return await t.execute()


async def tool_dream_memorize(content: str, source: str = "user") -> dict:
    t = DreamMemorizeTool()
    return await t.execute(content=content, source=source)


async def tool_dream_summary() -> dict:
    t = DreamSummaryTool()
    return await t.execute()
