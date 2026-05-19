"""Dream State Processor tools — unconscious idea generation and memory consolidation."""

from nikto.tools.base import Tool

_dream = None

def _set_dream_engine(de):
    global _dream
    _dream = de

def _get_de():
    global _dream
    if _dream is None:
        from nikto.dream.engine import DreamEngine
        _dream = DreamEngine()
    return _dream


async def tool_dream_force() -> str:
    de = _get_de()
    insights = de.force_dream()
    if not insights:
        return "Dream cycle produced no insights."
    lines = [f"Dream cycle complete — {len(insights)} insights:"]
    for ins in insights:
        lines.append(f"  [{ins['type']}] (confidence: {ins['confidence']:.0%}) {ins['content'][:150]}")
    return "\n".join(lines)


async def tool_dream_insights(count: int = 10) -> str:
    de = _get_de()
    insights = de.get_insights(count)
    if not insights:
        return "No dream insights yet. Use dream_force to generate insights."
    lines = [f"Recent dream insights ({len(insights)}):"]
    for ins in insights:
        lines.append(f"  [{ins['type']}] {ins['content'][:120]}")
    return "\n".join(lines)


async def tool_dream_memorize(source: str, content: str) -> str:
    de = _get_de()
    de.consolidator.record_memory(source, content)
    total = de.consolidator.count()
    return f"Memory recorded from '{source}'. Total consolidated memories: {total}"


async def tool_dream_summary() -> str:
    de = _get_de()
    s = de.summary()
    themes = de.consolidator.consolidate()
    lines = [
        f"Dream State Summary:",
        f"  Status:     {'RUNNING' if s['running'] else 'STOPPED'}",
        f"  Dreams:     {s['dream_count']}",
        f"  Insights:   {s['total_insights']}",
        f"  Memories:   {s['memories_consolidated']}",
        f"  Types:      {', '.join(s['insight_types'])}",
    ]
    if themes:
        lines.append("  Patterns:")
        for t in themes[:3]:
            lines.append(f"    - {t}")
    return "\n".join(lines)


DreamForceTool = Tool(name="dream_force", description="Force an immediate dream cycle. NIKTO processes consolidated memories, discovers hidden patterns, and generates novel creative ideas. Returns insights with confidence scores.", parameters={"type": "object", "properties": {}}, async_function=tool_dream_force)
DreamInsightsTool = Tool(name="dream_insights", description="View recent dream insights: creative ideas, pattern discoveries, and memory consolidations from NIKTO's unconscious processing.", parameters={"type": "object", "properties": {
    "count": {"type": "integer", "description": "Number of recent insights to show"},
}}, async_function=tool_dream_insights)
DreamMemorizeTool = Tool(name="dream_memorize", description="Record an experience or memory into NIKTO's dream state processor. These memories are consolidated during dream cycles to discover patterns and generate insights.", parameters={"type": "object", "properties": {
    "source": {"type": "string", "description": "Source of the memory (e.g., 'user_conversation', 'autopilot_task')"},
    "content": {"type": "string", "description": "The memory content to store"},
}, "required": ["source", "content"]}, async_function=tool_dream_memorize)
DreamSummaryTool = Tool(name="dream_summary", description="Get a summary of the dream state processor: number of dreams, insights, consolidated memories, and discovered patterns.", parameters={"type": "object", "properties": {}}, async_function=tool_dream_summary)
