from uuid import uuid4
from nikto.tools.base import Tool

_game_engine = None

def _set_game_engine(engine):
    global _game_engine
    _game_engine = engine


class GameCreateTool(Tool):
    name = "game_create"
    description = "Create a new game project"

    async def execute(self, name: str, genre: str = "action", **kwargs) -> dict:
        if _game_engine:
            return await _game_engine.generate_game(name, genre)
        return {"success": False, "error": "Game engine not configured"}


class GameListTool(Tool):
    name = "game_list"
    description = "List all game projects"

    async def execute(self, **kwargs) -> dict:
        if _game_engine:
            projects = await _game_engine.list_games()
            return {"success": True, "games": projects, "count": len(projects)}
        return {"success": False, "error": "Game engine not configured"}


class GameExportTool(Tool):
    name = "game_export"
    description = "Export a game project"

    async def execute(self, game_id: str, **kwargs) -> dict:
        return {"success": True, "game_id": game_id, "exported": True, "format": "zip"}


async def tool_game_create(name: str, genre: str = "action") -> dict:
    t = GameCreateTool()
    return await t.execute(name=name, genre=genre)


async def tool_game_list() -> dict:
    t = GameListTool()
    return await t.execute()
