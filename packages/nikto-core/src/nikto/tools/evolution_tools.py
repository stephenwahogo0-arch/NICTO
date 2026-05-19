"""Self-Evolution tools — NIKTO heals, optimizes, and benchmarks itself."""

from nikto.tools.base import Tool

_evolution = None

def _set_evolution(ev):
    global _evolution
    _evolution = ev

def _get_ev():
    global _evolution
    if _evolution is None:
        from nikto.evolution.engine import EvolutionEngine
        _evolution = EvolutionEngine()
    return _evolution


async def tool_evolution_health() -> str:
    from nikto.evolution.engine import SelfHealer
    results = await SelfHealer.heal_all()
    lines = ["Self-Health Check Results:"]
    for r in results:
        lines.append(f"  [{ 'OK' if r.success else 'FAIL' }] {r.action}: {r.output[:100]}")
    return "\n".join(lines)


async def tool_evolution_analyze(module_path: str) -> str:
    from nikto.evolution.engine import SelfOptimizer
    analysis = await SelfOptimizer.analyze_module(module_path)
    lines = [f"Analysis of {module_path}:"]
    lines.append(f"  Lines: {analysis['lines']}")
    lines.append(f"  Issues: {analysis['issue_count']}")
    lines.append(f"  Score: {analysis['optimization_score']}/100")
    for issue in analysis.get("issues", [])[:5]:
        lines.append(f"  - [{issue['type']}] Line {issue['line']}: {str(issue.get('text', issue.get('length', '')))[:60]}")
    return "\n".join(lines)


async def tool_evolution_suggest(module_path: str) -> str:
    from nikto.evolution.engine import SelfOptimizer
    suggestions = await SelfOptimizer.suggest_improvements(module_path)
    if not suggestions:
        return f"No suggestions for {module_path}"
    lines = [f"Suggestions for {module_path}:"]
    for s in suggestions:
        lines.append(f"  [{s['priority']}] Line {s['line']}: {s['suggestion']}")
    return "\n".join(lines)


async def tool_evolution_benchmark() -> str:
    from nikto.evolution.engine import BenchmarkSuite
    results = await BenchmarkSuite.run_all()
    lines = ["NIKTO Benchmark Results:"]
    for name, data in results.items():
        if isinstance(data, dict):
            items = " | ".join(f"{k}={v}" for k, v in data.items())
            lines.append(f"  {name}: {items}")
    return "\n".join(lines)


EvolutionHealthTool = Tool(name="evolution_health", description="Run a complete self-health check on NIKTO's codebase. Checks for broken imports, syntax errors, and missing __init__.py files. Auto-heals issues found.", parameters={"type": "object", "properties": {}}, async_function=tool_evolution_health)
EvolutionAnalyzeTool = Tool(name="evolution_analyze", description="Analyze any NIKTO module for code quality issues: wildcard imports, empty functions, long lines, TODOs. Returns optimization score out of 100.", parameters={"type": "object", "properties": {
    "module_path": {"type": "string", "description": "Relative path within nikto package (e.g., 'tools/device_control.py')"},
}, "required": ["module_path"]}, async_function=tool_evolution_analyze)
EvolutionSuggestTool = Tool(name="evolution_suggest", description="Get intelligent improvement suggestions for any NIKTO module. Recommends refactoring, optimizations, and fixes.", parameters={"type": "object", "properties": {
    "module_path": {"type": "string", "description": "Relative path within nikto package"},
}, "required": ["module_path"]}, async_function=tool_evolution_suggest)
EvolutionBenchmarkTool = Tool(name="evolution_benchmark", description="Run performance benchmarks across NIKTO's systems: import speed, memory usage, tool registry throughput.", parameters={"type": "object", "properties": {}}, async_function=tool_evolution_benchmark)
