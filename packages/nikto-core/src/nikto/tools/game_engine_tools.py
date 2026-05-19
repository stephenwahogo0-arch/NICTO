"""Nikto Game Engine tools — generate 3D games from prompts."""

from nikto.tools.base import Tool

_game_engine = None

def _set_game_engine(ge):
    global _game_engine
    _game_engine = ge

def _get_ge():
    global _game_engine
    if _game_engine is None:
        from nikto.game_engine.engine import GameEngine
        _game_engine = GameEngine()
    return _game_engine


async def tool_game_create(prompt: str, title: str = "", genre: str = "", resolution: str = "1920x1080") -> str:
    ge = _get_ge()
    result = await ge.generate_game(prompt, title=title, genre=genre, resolution=resolution)
    if result["success"]:
        lines = [
            f"[GAME] {result['title']} created!",
            f"  Genre:     {result['genre']}",
            f"  Resolution: {result['resolution']}",
            f"  Path:      {result['output_path']}",
            f"  Assets:    {result['assets_count']}",
            f"  Message:   {result['message']}",
        ]
        return "\n".join(lines)
    return f"Game generation failed: {result.get('error', 'unknown error')}"


async def tool_game_list() -> str:
    ge = _get_ge()
    games = await ge.list_games()
    if not games:
        return "No games generated yet. Use game_create to build a 3D game from a prompt."
    lines = [f"Generated games ({len(games)}):"]
    for g in games:
        lines.append(f"  [{g['project_id'][:8]}] {g['title']} ({g['genre']}, {g['resolution']})")
    return "\n".join(lines)


async def tool_game_export(project_id: str, export_format: str = "windows") -> str:
    ge = _get_ge()
    result = await ge.export_game(project_id, export_format)
    if result["success"]:
        return f"Game '{project_id}' ready for export to {export_format}. Path: {result['project_path']}"
    return f"Export failed: {result.get('error', 'unknown')}"


GameCreateTool = Tool(name="game_create", description="Generate a complete 3D video game from a text prompt. Supports racing, FPS, battle royale, open world, platformer, RPG, strategy, simulation, and puzzle genres. Creates a full Godot 4.3 project with scenes, scripts, and input configuration.", parameters={"type": "object", "properties": {
    "prompt": {"type": "string", "description": "Description of the game to create (e.g., 'a futuristic racing game with neon tracks and turbo boosts')"},
    "title": {"type": "string", "description": "Game title (auto-generated if empty)"},
    "genre": {"type": "string", "enum": ["racing", "fps", "battle_royale", "open_world", "platformer", "rpg", "strategy", "simulation", "puzzle", "custom"], "description": "Game genre"},
    "resolution": {"type": "string", "description": "Screen resolution (e.g., 1920x1080, 3840x2160)"},
}, "required": ["prompt"]}, async_function=tool_game_create)
GameListTool = Tool(name="game_list", description="List all generated game projects with their titles, genres, and project IDs.", parameters={"type": "object", "properties": {}}, async_function=tool_game_list)
GameExportTool = Tool(name="game_export", description="Export a generated game project for distribution on Windows, Linux, or web.", parameters={"type": "object", "properties": {
    "project_id": {"type": "string", "description": "Project ID from game_list"},
    "export_format": {"type": "string", "enum": ["windows", "linux", "web"], "description": "Target platform"},
}, "required": ["project_id"]}, async_function=tool_game_export)
