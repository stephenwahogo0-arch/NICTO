from enum import Enum
from uuid import uuid4
from datetime import datetime


class GameGenre(Enum):
    ACTION = "action"
    RPG = "rpg"
    STRATEGY = "strategy"
    PUZZLE = "puzzle"
    PLATFORMER = "platformer"
    SIMULATION = "simulation"
    RACING = "racing"


class GameProject:
    def __init__(self, name: str, genre: GameGenre):
        self.id = str(uuid4())[:12]
        self.name = name
        self.genre = genre
        self.created_at = datetime.now().isoformat()
        self.files = {}


class ProjectGenerator:
    @staticmethod
    def generate_pygame_project(project: GameProject) -> dict:
        main_code = f'''import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("{project.name}")
clock = pygame.time.Clock()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
'''
        project.files["main.py"] = main_code
        return {"success": True, "project_id": project.id, "files": list(project.files.keys())}


class GameEngine:
    def __init__(self):
        self._projects = {}

    async def generate_game(self, name: str, genre: str = "action") -> dict:
        try:
            g = GameGenre(genre)
        except ValueError:
            g = GameGenre.ACTION
        project = GameProject(name, g)
        generator = ProjectGenerator()
        result = generator.generate_pygame_project(project)
        self._projects[project.id] = project
        return {**result, "name": name, "genre": g.value, "created_at": project.created_at}

    async def list_games(self) -> list[dict]:
        return [{"id": p.id, "name": p.name, "genre": p.genre.value, "created_at": p.created_at, "files": list(p.files.keys())} for p in self._projects.values()]
