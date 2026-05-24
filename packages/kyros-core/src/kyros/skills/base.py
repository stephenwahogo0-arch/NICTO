from typing import Optional


class SkillRuntime:
    def __init__(self):
        self._skills = {}

    def register(self, name: str, func, description: str = ""):
        self._skills[name] = {"func": func, "description": description}

    def list_skills(self) -> list[dict]:
        return [{"name": name, "description": info["description"]} for name, info in self._skills.items()]

    def execute(self, name: str, **kwargs) -> dict:
        skill = self._skills.get(name)
        if not skill:
            return {"success": False, "error": f"Skill '{name}' not found"}
        try:
            result = skill["func"](**kwargs)
            return {"success": True, "result": result, "skill": name}
        except Exception as e:
            return {"success": False, "error": str(e)}
