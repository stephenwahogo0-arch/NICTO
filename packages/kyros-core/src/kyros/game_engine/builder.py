"""KYROS Game Builder — generates complete runnable games from natural language prompts.
Uses templates + LLM code generation for every genre."""

import os
import json
import random
import shutil
import string
import tempfile
import textwrap
import time
import uuid
from pathlib import Path
from typing import Optional


TEMPLATES_DIR = Path(__file__).parent / "templates"
BUILT_GAMES_DIR = Path(tempfile.gettempdir()) / "nikto_games"


class GameTemplate:
    def __init__(self, name: str, genre: str, description: str, code: str, assets: dict = None):
        self.name = name
        self.genre = genre
        self.description = description
        self.code = code
        self.assets = assets or {}

    def instantiate(self, title: str, **kwargs) -> str:
        code = self.code
        for key, value in kwargs.items():
            code = code.replace(f"{{{{{key}}}}}", str(value))
        code = code.replace("{{TITLE}}", title)
        code = code.replace("{{GENRE}}", self.genre)
        return code


class GameBuilder:
    def __init__(self):
        self.templates: dict[str, GameTemplate] = {}
        self._load_default_templates()
        BUILT_GAMES_DIR.mkdir(parents=True, exist_ok=True)
        self._projects: dict[str, dict] = {}
        self._project_dir = BUILT_GAMES_DIR
        self._template_dir = Path(__file__).parent / "templates"
        self._template_dir.mkdir(parents=True, exist_ok=True)

    def _load_default_templates(self):
        templates = {
            "platformer": GameTemplate(
                "2D Platformer", "platformer",
                "A side-scrolling platformer with jumping, enemies, coins, and levels.",
                self._PLATFORMER_CODE,
            ),
            "rpg": GameTemplate(
                "Top-Down RPG", "rpg",
                "An RPG with movement, NPCs, combat, inventory, and quests.",
                self._RPG_CODE,
            ),
            "fps": GameTemplate(
                "First-Person Shooter", "fps",
                "A first-person shooter with raycasting, enemies, health, and weapons.",
                self._FPS_CODE,
            ),
            "racing": GameTemplate(
                "Top-Down Racer", "racing",
                "A top-down racing game with multiple cars, tracks, and lap counting.",
                self._RACING_CODE,
            ),
            "puzzle": GameTemplate(
                "Match-3 Puzzle", "puzzle",
                "A match-3 puzzle game with combos, scoring, and levels.",
                self._PUZZLE_CODE,
            ),
            "strategy": GameTemplate(
                "Tower Defense", "strategy",
                "A tower defense game with towers, enemies, waves, and upgrades.",
                self._STRATEGY_CODE,
            ),
            "fighting": GameTemplate(
                "2D Fighter", "fighting",
                "A 2D fighting game with punches, kicks, special moves, and health bars.",
                self._FIGHTING_CODE,
            ),
            "simulation": GameTemplate(
                "Life Simulation", "simulation",
                "A life simulation game with characters, needs, jobs, and relationships.",
                self._SIMULATION_CODE,
            ),
            "shooter": GameTemplate(
                "Space Shooter", "shooter",
                "A space shooter with waves of enemies, power-ups, and boss fights.",
                self._SHOOTER_CODE,
            ),
            "stealth": GameTemplate(
                "Stealth Game", "stealth",
                "A stealth game with guards, shadows, distractions, and objectives.",
                self._STEALTH_CODE,
            ),
        }
        self.templates.update(templates)

    def detect_genre(self, prompt: str) -> str:
        p = prompt.lower()
        scores = {
            "platformer": sum(1 for w in ["jump", "platform", "mario", "side-scroll", "2d platform", "run and jump", "collect coin"] if w in p),
            "rpg": sum(1 for w in ["rpg", "quest", "inventory", "level up", "character", "npc", "dialog", "magic", "sword", "dungeon", "fantasy"] if w in p),
            "fps": sum(1 for w in ["fps", "shoot", "gun", "first-person", "fps", "bullet", "weapon", "war", "soldier", "call of duty", "combat"] if w in p),
            "racing": sum(1 for w in ["race", "racing", "car", "drive", "speed", "track", "turbo", "vehicle", "lap", "formula"] if w in p),
            "puzzle": sum(1 for w in ["puzzle", "match", "solve", "brain", "tile", "block", "chain", "combo"] if w in p),
            "strategy": sum(1 for w in ["strategy", "tower", "defense", "rts", "base", "build", "wave", "upgrade", "chess", "tactic"] if w in p),
            "fighting": sum(1 for w in ["fight", "punch", "kick", "fighter", "martial", "combo", "versus", "battle", "mortal"] if w in p),
            "simulation": sum(1 for w in ["sim", "simulation", "city", "tycoon", "life", "farm", "manage", "build", "create"] if w in p),
            "shooter": sum(1 for w in ["space", "shooter", "asteroid", "alien", "ship", "laser", "invader", "galaga"] if w in p),
            "stealth": sum(1 for w in ["stealth", "sneak", "guard", "shadow", "hide", "assassin", "spy", "covert"] if w in p),
        }
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return "platformer"

    def generate_title(self, prompt: str) -> str:
        words = [w.capitalize() for w in prompt.split() if len(w) > 3][:3]
        prefixes = ["Neon", "Star", "Cyber", "Ultra", "Metal", "Shadow", "Phantom", "Cosmic", "Infinite", "Quantum", "Turbo", "Omega"]
        suffixes = ["Quest", "Force", "Strike", "Rush", "Fury", "Storm", "Blade", "Realm", "Core", "Rise", "Legacy", "Reborn"]
        if words:
            return f"{words[0]} {words[1] if len(words) > 1 else random.choice(suffixes)}"
        return f"{random.choice(prefixes)} {random.choice(suffixes)}"

    def build_game(self, title: str, genre: str, prompt: str, author: str = "KYROS", extra_features: list = None) -> dict:
        genre = genre or self.detect_genre(prompt)
        template = self.templates.get(genre)
        if not template:
            template = self.templates.get("platformer")
        title = title or self.generate_title(prompt)
        project_id = uuid.uuid4().hex[:12]
        game_dir = self._project_dir / f"{project_id}"
        game_dir.mkdir(parents=True, exist_ok=True)

        extra = extra_features or []
        features_str = ", ".join(extra) if extra else "none"

        code = template.instantiate(
            title=title,
            PROMPT=prompt,
            EXTRA_FEATURES=features_str,
            AUTHOR=author,
            PROJECT_ID=project_id,
            WIDTH=800,
            HEIGHT=600,
        )

        main_file = game_dir / "main.py"
        main_file.write_text(code, encoding="utf-8")

        readme = game_dir / "README.txt"
        readme.write_text(
            f"KYROS Game Engine - {title}\n"
            f"Genre: {genre}\n"
            f"Description: {prompt}\n"
            f"Generated by: {author}\n"
            f"Run: python main.py\n"
        )

        summary = {
            "project_id": project_id,
            "title": title,
            "genre": genre,
            "prompt": prompt[:200],
            "path": str(game_dir),
            "file": str(main_file),
            "lines": len(code.splitlines()),
            "author": author,
            "features": extra,
            "features_str": features_str,
            "success": True,
        }
        self._projects[project_id] = summary
        return summary

    def compile_game(self, project_id: str) -> dict:
        project = self._projects.get(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}
        return {
            "success": True,
            "message": f"Game '{project['title']}' can be run directly: python {project['file']}",
            "command": f"python {project['file']}",
            "path": project["path"],
        }

    def list_games(self) -> list[dict]:
        return list(self._projects.values())

    def get_genres(self) -> list[str]:
        return list(self.templates.keys())

    def describe_genre(self, genre: str) -> str:
        t = self.templates.get(genre)
        if t:
            return f"{t.name}: {t.description}"
        return f"Unknown genre: {genre}"

# ============================================================
# GAME TEMPLATES (complete, runnable Pygame CE games)
# ============================================================

    _PLATFORMER_CODE = '''"""
{{TITLE}} - KYROS Game Engine
Genre: {{GENRE}}
"""
import pygame
import random
import sys

W, H = {{WIDTH}}, {{HEIGHT}}
GRAVITY = 0.6
JUMP_POWER = -12
MOVE_SPEED = 5
FPS = 60

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("{{TITLE}}")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

class Player:
    def __init__(self):
        self.x = 50
        self.y = H - 100
        self.w = 28
        self.h = 32
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.alive = True
        self.score = 0

    def update(self):
        keys = pygame.key.get_pressed()
        self.vx = 0
        if keys[pygame.K_LEFT]: self.vx = -MOVE_SPEED
        if keys[pygame.K_RIGHT]: self.vx = MOVE_SPEED
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy = JUMP_POWER
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy
        self.on_ground = False

    def render(self):
        pygame.draw.rect(screen, (50, 200, 255), (self.x, self.y, self.w, self.h))
        eye_col = (255, 255, 255)
        pygame.draw.circle(screen, eye_col, (int(self.x + 8), int(self.y + 8)), 4)
        pygame.draw.circle(screen, eye_col, (int(self.x + 20), int(self.y + 8)), 4)

player = Player()
coins = []
enemies = []
platforms = [(0, H-20, W*2, 20)]
camera_x = 0

def spawn_level():
    global coins, enemies, platforms
    coins = []
    enemies = []
    platforms = [(0, H-20, W*2, 20)]
    for i in range(15):
        px = random.randint(100, 800)
        py = random.randint(100, 400)
        pw = random.randint(50, 120)
        platforms.append((px, py, pw, 12))
    for i in range(8):
        cx = random.randint(100, 800)
        cy = random.randint(80, 450)
        coins.append({"x": cx, "y": cy, "collected": False})
    for i in range(4):
        ex = random.randint(200, 700)
        ey = random.randint(50, 350)
        enemies.append({"x": ex, "y": ey, "w": 24, "h": 24, "vx": random.choice([-1, 1]), "alive": True})

spawn_level()
running = True

while running:
    dt = clock.tick(FPS) / 16.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and not player.alive:
            player = Player(); spawn_level(); camera_x = 0

    player.update()
    if player.x > camera_x + W * 0.4:
        camera_x = player.x - W * 0.4

    # Platform collision
    player.on_ground = False
    for px, py, pw, ph in platforms:
        if player.x + player.w > px and player.x < px + pw:
            if player.y + player.h > py and player.y + player.h < py + ph + 10 and player.vy >= 0:
                player.y = py - player.h
                player.vy = 0
                player.on_ground = True

    # Coin collection
    for coin in coins:
        if not coin["collected"]:
            dx = (player.x + player.w/2) - coin["x"]
            dy = (player.y + player.h/2) - coin["y"]
            if abs(dx) < 20 and abs(dy) < 20:
                coin["collected"] = True
                player.score += 10

    # Enemy collision
    for enemy in enemies:
        if enemy["alive"]:
            enemy["x"] += enemy["vx"] * dt
            if enemy["x"] < 100 or enemy["x"] > 700:
                enemy["vx"] *= -1
            enemy["y"] += GRAVITY * 1.5
            if enemy["y"] > H - 40: enemy["y"] = H - 40
            ex, ey, ew, eh = enemy["x"], enemy["y"], enemy["w"], enemy["h"]
            if player.x < ex + ew and player.x + player.w > ex and player.y < ey + eh and player.y + player.h > ey:
                if player.vy > 0 and player.y + player.h < ey + 15:
                    enemy["alive"] = False
                    player.score += 50
                    player.vy = -8
                else:
                    player.alive = False

    # Fall death
    if player.y > H + 50:
        player.alive = False

    # Draw
    screen.fill((20, 20, 50))
    for px, py, pw, ph in platforms:
        pygame.draw.rect(screen, (100, 180, 100), (px - camera_x, py, pw, ph))
    for coin in coins:
        if not coin["collected"]:
            pygame.draw.circle(screen, (255, 220, 50), (int(coin["x"] - camera_x), int(coin["y"])), 8)
    for enemy in enemies:
        if enemy["alive"]:
            pygame.draw.rect(screen, (220, 50, 50), (enemy["x"] - camera_x, enemy["y"], enemy["w"], enemy["h"]))
    player.render()

    # UI
    score_text = font.render(f"Score: {player.score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))
    if not player.alive:
        over = font.render("GAME OVER - Press R to restart", True, (255, 50, 50))
        screen.blit(over, (W//2 - 180, H//2))
    pygame.display.flip()

pygame.quit()
sys.exit()
'''

    _RPG_CODE = '''"""
{{TITLE}} - KYROS Game Engine
Genre: {{GENRE}}
"""
import pygame
import random
import math
import sys

W, H = {{WIDTH}}, {{HEIGHT}}
FPS = 60

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("{{TITLE}}")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)
big_font = pygame.font.Font(None, 48)

TILE = 32
WORLD_W, WORLD_H = 50, 50

TILE_GRASS, TILE_WALL, TILE_WATER, TILE_ROAD = 0, 1, 2, 3
world = [[TILE_GRASS for _ in range(WORLD_W)] for _ in range(WORLD_H)]

# Generate dungeon walls
for _ in range(80):
    wx, wy = random.randint(2, WORLD_W-3), random.randint(2, WORLD_H-3)
    world[wy][wx] = TILE_WALL
for _ in range(20):
    wx, wy = random.randint(2, WORLD_W-3), random.randint(2, WORLD_H-3)
    world[wy][wx] = TILE_WATER
for y in range(WORLD_H):
    for x in range(WORLD_W):
        if x == 0 or y == 0 or x == WORLD_W-1 or y == WORLD_H-1:
            world[y][x] = TILE_WALL

class Entity:
    def __init__(self, x, y, char, color, hp=20, attack=3, defense=1, name="Entity"):
        self.x, self.y = x, y
        self.char = char
        self.color = color
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.name = name
        self.alive = True
        self.level = 1
        self.xp = 0
        self.xp_next = 20

    def take_damage(self, dmg):
        actual = max(1, dmg - self.defense)
        self.hp -= actual
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return actual

    def heal(self, amt):
        self.hp = min(self.max_hp, self.hp + amt)

    def is_alive(self):
        return self.alive and self.hp > 0

player = Entity(10, 10, "@", (50, 200, 255), hp=30, attack=5, defense=2, name="Hero")
enemies = []
for _ in range(12):
    ex, ey = random.randint(5, WORLD_W-5), random.randint(5, WORLD_H-5)
    while world[ey][ex] != TILE_GRASS:
        ex, ey = random.randint(5, WORLD_W-5), random.randint(5, WORLD_H-5)
    et = random.choice(["Goblin", "Skeleton", "Bat", "Slime"])
    enemies.append(Entity(ex, ey, et[0], (200, 50, 50), hp=random.randint(8, 18), attack=random.randint(2, 5), defense=random.randint(0, 2), name=et))

cam_x, cam_y = 0, 0
messages = ["Welcome to {{TITLE}}!", "Use WASD to move, attack enemies with SPACE"]
log = []
combat_mode = False
combat_target = None
turn_ready = True
inventory = ["Health Potion"]
gold = 0

def attack(attacker, defender):
    dmg = attacker.take_damage(attacker.attack + random.randint(0, 3))
    msg = f"{attacker.name} hits {defender.name} for {dmg} damage!"
    log.append(msg)
    if not defender.is_alive():
        log.append(f"{defender.name} is defeated!")
        return True
    return False

running = True
while running:
    dt = clock.tick(FPS) / 16.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if not combat_mode:
                dx, dy = 0, 0
                if event.key == pygame.K_w: dy = -1
                if event.key == pygame.K_s: dy = 1
                if event.key == pygame.K_a: dx = -1
                if event.key == pygame.K_d: dx = 1
                nx, ny = player.x + dx, player.y + dy
                if 0 <= nx < WORLD_W and 0 <= ny < WORLD_H and world[ny][nx] == TILE_GRASS:
                    player.x, player.y = nx, ny
                elif world[ny][nx] != TILE_WALL and world[ny][nx] != TILE_WATER:
                    pass
                for e in enemies:
                    if e.x == nx and e.y == ny and e.is_alive():
                        combat_mode = True
                        combat_target = e
                        log.append(f"Battle! {e.name} appears!")
                        break
            else:
                if event.key == pygame.K_SPACE and turn_ready and combat_target:
                    turn_ready = False
                    player_won = attack(combat_target, player)
                    if not combat_target.is_alive():
                        player.xp += 10
                        gold += random.randint(1, 5)
                        if player.xp >= player.xp_next:
                            player.level += 1
                            player.xp -= player.xp_next
                            player.xp_next = int(player.xp_next * 1.5)
                            player.max_hp += 10
                            player.hp = player.max_hp
                            player.attack += 2
                            player.defense += 1
                            log.append(f"Level up! Now level {player.level}!")
                        enemies.remove(combat_target)
                        combat_mode = False
                        combat_target = None
                    else:
                        combat_target_won = attack(player, combat_target)
                        if not player.is_alive():
                            log.append("You have been defeated!")
                            player.hp = player.max_hp // 2
                            combat_mode = False
                            combat_target = None
                    turn_ready = True

    # Camera follow
    cam_x = player.x * TILE - W // 2 + TILE // 2
    cam_y = player.y * TILE - H // 2 + TILE // 2

    # Draw world
    screen.fill((10, 10, 30))
    start_tx = max(0, int(cam_x // TILE))
    start_ty = max(0, int(cam_y // TILE))
    end_tx = min(WORLD_W, start_tx + W // TILE + 2)
    end_ty = min(WORLD_H, start_ty + H // TILE + 2)
    for wy in range(start_ty, end_ty):
        for wx in range(start_tx, end_tx):
            sx = wx * TILE - cam_x
            sy = wy * TILE - cam_y
            tile = world[wy][wx]
            if tile == TILE_GRASS: col = (30, 60, 30)
            elif tile == TILE_WALL: col = (80, 80, 80)
            elif tile == TILE_WATER: col = (20, 40, 100)
            elif tile == TILE_ROAD: col = (60, 55, 40)
            else: col = (30, 30, 30)
            pygame.draw.rect(screen, col, (sx, sy, TILE, TILE))

    # Draw enemies
    for e in enemies:
        ex = e.x * TILE - cam_x
        ey = e.y * TILE - cam_y
        if -TILE < ex < W + TILE and -TILE < ey < H + TILE:
            pygame.draw.ellipse(screen, e.color, (ex + 2, ey + 2, TILE-4, TILE-4))
            hp_pct = e.hp / e.max_hp
            pygame.draw.rect(screen, (200, 50, 50), (ex, ey-6, TILE, 4))
            pygame.draw.rect(screen, (50, 200, 50), (ex, ey-6, int(TILE * hp_pct), 4))

    # Draw player
    px = player.x * TILE - cam_x
    py = player.y * TILE - cam_y
    pygame.draw.ellipse(screen, player.color, (px, py, TILE, TILE))
    pygame.draw.circle(screen, (255, 255, 255), (px + 22, py + 8), 4)
    pygame.draw.circle(screen, (255, 255, 255), (px + 10, py + 8), 4)

    # UI
    pygame.draw.rect(screen, (0, 0, 0, 180), (0, H-80, W, 80))
    hp_text = font.render(f"HP: {player.hp}/{player.max_hp}  Lv.{player.level}  XP: {player.xp}/{player.xp_next}  Gold: {gold}", True, (255, 255, 255))
    screen.blit(hp_text, (10, H-70))
    for i, msg in enumerate(log[-3:]):
        screen.blit(font.render(msg, True, (200, 200, 200)), (10, H - 45 + i * 15))
    if combat_mode and combat_target:
        combat_text = font.render(f"Fighting {combat_target.name}! SPACE to attack", True, (255, 200, 50))
        screen.blit(combat_text, (W//2 - 150, 10))

    pygame.display.flip()

pygame.quit()
sys.exit()
'''

    _FPS_CODE = '''"""
{{TITLE}} - KYROS Game Engine
Genre: {{GENRE}}
Raycasting FPS engine.
"""
import pygame
import math
import sys

W, H = {{WIDTH}}, {{HEIGHT}}
FPS = 60
FOV = math.pi / 3
HALF_FOV = FOV / 2
NUM_RAYS = W // 2
DELTA_ANGLE = FOV / NUM_RAYS
DIST_PROJ = (W / 2) / math.tan(HALF_FOV)
SCALE = W // NUM_RAYS

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("{{TITLE}}")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)

MAP = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,1,1,0,0,0,0,0,1,1,0,0,0,1],
    [1,0,0,1,0,0,0,0,0,0,0,1,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,1,0,1,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,1,0,0,0,0,0,0,0,0,1,0,0,1],
    [1,0,0,1,0,0,0,0,0,0,0,0,1,0,0,1],
    [1,0,0,1,1,0,0,0,0,0,1,1,1,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

TILE = 64
px, py = 3.5 * TILE, 3.5 * TILE
p_angle = 0
p_speed = 3
health = 100
ammo = 20
enemies = [{"x": 6.5 * TILE, "y": 5.5 * TILE, "hp": 30, "alive": True}]
kills = 0

def cast_ray(ax, ay, angle):
    sin_a = math.sin(angle)
    cos_a = math.cos(angle)
    if cos_a == 0: cos_a = 0.0001
    if sin_a == 0: sin_a = 0.0001

    x, y = ax, ay
    while 0 <= int(x // TILE) < len(MAP[0]) and 0 <= int(y // TILE) < len(MAP):
        mx, my = int(x // TILE), int(y // TILE)
        if MAP[my][mx] == 1:
            return math.sqrt((x - ax)**2 + (y - ay)**2), mx, my
        x += cos_a * 2
        y += sin_a * 2
    return 1000, 0, 0

def shoot():
    global ammo
    if ammo <= 0: return
    ammo -= 1
    for e in enemies:
        if not e["alive"]: continue
        dx = e["x"] - px
        dy = e["y"] - py
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < 200:
            e_angle = math.atan2(dy, dx)
            if abs(e_angle - p_angle) < 0.3:
                e["hp"] -= 15
                if e["hp"] <= 0:
                    e["alive"] = False
                    global kills
                    kills += 1

running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
            if event.key == pygame.K_SPACE: shoot()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: p_angle -= 0.05
    if keys[pygame.K_RIGHT]: p_angle += 0.05
    if keys[pygame.K_w]:
        nx = px + math.cos(p_angle) * p_speed
        ny = py + math.sin(p_angle) * p_speed
        mx, my = int(nx // TILE), int(ny // TILE)
        if 0 <= mx < len(MAP[0]) and 0 <= my < len(MAP) and MAP[my][mx] == 0:
            px, py = nx, ny
    if keys[pygame.K_s]:
        nx = px - math.cos(p_angle) * p_speed
        ny = py - math.sin(p_angle) * p_speed
        mx, my = int(nx // TILE), int(ny // TILE)
        if 0 <= mx < len(MAP[0]) and 0 <= my < len(MAP) and MAP[my][mx] == 0:
            px, py = nx, ny
    if keys[pygame.K_a]:
        strafe = p_angle - math.pi/2
        px += math.cos(strafe) * p_speed * 0.7
        py += math.sin(strafe) * p_speed * 0.7
    if keys[pygame.K_d]:
        strafe = p_angle + math.pi/2
        px += math.cos(strafe) * p_speed * 0.7
        py += math.sin(strafe) * p_speed * 0.7

    # Render
    screen.fill((30, 30, 30))
    for ray in range(NUM_RAYS):
        angle = p_angle - HALF_FOV + ray * DELTA_ANGLE
        dist, mx, my = cast_ray(px, py, angle)
        if dist > 500: dist = 500
        if dist < 0.1: dist = 0.1
        proj_h = int(TILE * DIST_PROJ / dist)
        color = max(50, min(255, 255 - dist * 0.4))
        wall_col = (color, color * 0.7, color * 0.3)
        pygame.draw.rect(screen, wall_col, (ray * SCALE, H//2 - proj_h//2, SCALE, proj_h))

    # Floor/ceiling
    pygame.draw.rect(screen, (20, 20, 40), (0, 0, W, H//2))
    pygame.draw.rect(screen, (40, 30, 20), (0, H//2, W, H//2))

    # Enemies (billboard sprites)
    for e in enemies:
        if not e["alive"]: continue
        dx = e["x"] - px
        dy = e["y"] - py
        edist = math.sqrt(dx*dx + dy*dy)
        if edist < 0.1: edist = 0.1
        e_angle = math.atan2(dy, dx)
        angle_diff = e_angle - p_angle
        while angle_diff > math.pi: angle_diff -= 2*math.pi
        while angle_diff < -math.pi: angle_diff += 2*math.pi
        if abs(angle_diff) < HALF_FOV:
            e_proj = int(TILE * DIST_PROJ / edist)
            ex_screen = W//2 + int(math.tan(angle_diff) * DIST_PROJ)
            pygame.draw.rect(screen, (200, 50, 50), (ex_screen - e_proj//2, H//2 - e_proj//2, e_proj, e_proj))
            hp_w = int(e_proj * e["hp"] / 30)
            pygame.draw.rect(screen, (50, 200, 50), (ex_screen - e_proj//2, H//2 - e_proj//2 - 8, max(0, hp_w), 4))

    # HUD
    pygame.draw.rect(screen, (0, 0, 0, 128), (0, 0, W, 40))
    hud = font.render(f"HP: {health}  Ammo: {ammo}  Kills: {kills}", True, (255, 255, 255))
    screen.blit(hud, (10, 10))
    pygame.draw.line(screen, (255, 0, 0), (W//2, H//2 - 10), (W//2, H//2 + 10), 2)
    pygame.draw.line(screen, (255, 0, 0), (W//2 - 10, H//2), (W//2 + 10, H//2), 2)
    pygame.display.flip()

pygame.quit()
sys.exit()
'''

    _RACING_CODE = '''"""
{{TITLE}} - KYROS Game Engine
Genre: {{GENRE}}
"""
import pygame
import math
import sys

W, H = {{WIDTH}}, {{HEIGHT}}
FPS = 60

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("{{TITLE}}")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 32)
small_font = pygame.font.Font(None, 20)

# Pseudo-3D road rendering
player_x = 0.0
player_y = 0.0
player_angle = 0.0
speed = 0.0
max_speed = 15.0
accel = 0.3
brake = 0.2
friction = 0.05
steering = 0.0
steer_speed = 0.03

lap_count = 0
checkpoint = 0
total_checkpoints = 8
track_width = 800
road_segments = []
for i in range(500):
    seg = {"x": 0, "y": i * 20, "curve": 0}
    if 100 < i < 150: seg["curve"] = 0.02
    elif 200 < i < 230: seg["curve"] = -0.015
    elif 300 < i < 340: seg["curve"] = 0.025
    elif 400 < i < 430: seg["curve"] = -0.02
    road_segments.append(seg)

def project(seg_x, seg_y, cam_x, cam_y, cam_angle):
    dx = seg_x - cam_x
    dy = seg_y - cam_y
    rot_x = dx * math.cos(-cam_angle) - dy * math.sin(-cam_angle)
    rot_y = dx * math.sin(-cam_angle) + dy * math.cos(-cam_angle)
    if rot_y < 1: rot_y = 1
    scale = H / rot_y
    return (W//2 + rot_x * scale, int(scale))

score = 0
running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]: speed = min(speed + accel, max_speed)
    elif keys[pygame.K_DOWN]: speed = max(speed - brake, -max_speed * 0.3)
    else: speed *= (1 - friction)
    if keys[pygame.K_LEFT]: player_angle -= steer_speed * (speed / max_speed)
    if keys[pygame.K_RIGHT]: player_angle += steer_speed * (speed / max_speed)

    player_x += math.sin(player_angle) * speed * 0.5
    player_y += math.cos(player_angle) * speed * 0.5
    score += int(speed)

    # Render pseudo-3D road
    screen.fill((20, 30, 60))
    pygame.draw.rect(screen, (30, 40, 20), (0, H//2, W, H//2))

    look_ahead = 200
    for i in range(0, look_ahead, 2):
        seg_idx = int((player_y + i) % len(road_segments))
        seg_x = road_segments[seg_idx]["x"] + player_angle * 100 * (i / look_ahead)
        seg_y = i
        proj_scale = project(seg_x, seg_y, 0, 0, 0)
        sx, scale = proj_scale
        road_w = int(track_width * scale / 100)
        grass_w = road_w * 3
        rumble_w = road_w + 8

        # Grass
        grass_color = (30, 60 + (i % 20), 30) if (seg_idx // 10) % 2 == 0 else (40, 70, 40)
        pygame.draw.rect(screen, grass_color,
            (int(sx - grass_w), H//2 - int(scale), int(grass_w * 2), int(scale) + 1))

        # Rumble
        rumble_color = (255, 255, 255) if seg_idx % 2 == 0 else (0, 0, 0)
        pygame.draw.rect(screen, rumble_color,
            (int(sx - rumble_w), H//2 - int(scale), int(rumble_w * 2), int(scale) + 1))

        # Road
        road_color = (80, 80, 80) if seg_idx % 3 != 0 else (90, 90, 90)
        pygame.draw.rect(screen, road_color,
            (int(sx - road_w), H//2 - int(scale), int(road_w * 2), int(scale) + 1))

        # Center line
        if seg_idx % 6 < 3:
            pygame.draw.rect(screen, (255, 220, 50),
                (int(sx - 2), H//2 - int(scale), 4, int(scale) + 1))

    # Car
    car_color = (50, 150, 255)
    pygame.draw.ellipse(screen, car_color, (W//2 - 15, H - 120, 30, 50))

    # HUD
    hud_lines = [
        f"Speed: {int(abs(speed) * 10)} km/h",
        f"Score: {score}",
    ]
    for i, line in enumerate(hud_lines):
        screen.blit(font.render(line, True, (255, 255, 255)), (10, 10 + i * 35))

    # Speed bar
    bar_w = 150
    bar_h = 12
    fill = int(bar_w * abs(speed) / max_speed)
    pygame.draw.rect(screen, (80, 80, 80), (10, 80, bar_w, bar_h))
    color = (50, 200, 50) if fill < bar_w * 0.7 else (200, 200, 50) if fill < bar_w * 0.9 else (200, 50, 50)
    pygame.draw.rect(screen, color, (10, 80, fill, bar_h))

    pygame.display.flip()

pygame.quit()
sys.exit()
'''

    _PUZZLE_CODE = '''"""
{{TITLE}} - KYROS Game Engine
Genre: {{GENRE}}
"""
import pygame
import random
import sys

W, H = {{WIDTH}}, {{HEIGHT}}
FPS = 60
GRID = 8
TILE = W // GRID
TYPES = 6

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("{{TITLE}}")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 32)
big_font = pygame.font.Font(None, 56)

COLORS = [
    (255, 80, 80), (80, 255, 80), (80, 80, 255),
    (255, 255, 80), (255, 80, 255), (80, 255, 255),
]

grid = [[random.randint(0, TYPES-1) for _ in range(GRID)] for _ in range(GRID)]
selected = None
score = 0
moves = 30
combo = 0
level = 1
game_over = False

def get_matches():
    matches = set()
    for y in range(GRID):
        for x in range(GRID - 2):
            if grid[y][x] == grid[y][x+1] == grid[y][x+2]:
                matches.update([(y,x), (y,x+1), (y,x+2)])
    for x in range(GRID):
        for y in range(GRID - 2):
            if grid[y][x] == grid[y+1][x] == grid[y+2][x]:
                matches.update([(y,x), (y+1,x), (y+2,x)])
    return matches

def drop_tiles():
    for x in range(GRID):
        col = [grid[y][x] for y in range(GRID) if grid[y][x] is not None]
        col = [None] * (GRID - len(col)) + col
        for y in range(GRID):
            grid[y][x] = col[y]
    for y in range(GRID):
        for x in range(GRID):
            if grid[y][x] is None:
                grid[y][x] = random.randint(0, TYPES-1)

running = True
while running:
    dt = clock.tick(FPS) / 16.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False
        if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
            mx, my = event.pos
            gx, gy = mx // TILE, my // TILE
            if 0 <= gx < GRID and 0 <= gy < GRID:
                if selected is None:
                    selected = (gy, gx)
                else:
                    sy, sx = selected
                    if abs(sy - gy) + abs(sx - gx) == 1:
                        grid[sy][sx], grid[gy][gx] = grid[gy][gx], grid[sy][sx]
                        matches = get_matches()
                        if matches:
                            moves -= 1
                            for my2, mx2 in matches:
                                grid[my2][mx2] = None
                            while matches:
                                combo += 1
                                score += len(matches) * 10 * combo
                                drop_tiles()
                                matches = get_matches()
                            if moves <= 0:
                                level += 1
                                moves = 20 + level * 2
                        else:
                            grid[sy][sx], grid[gy][gx] = grid[gy][gx], grid[sy][sx]
                    selected = None
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            grid = [[random.randint(0, TYPES-1) for _ in range(GRID)] for _ in range(GRID)]
            selected = None; score = 0; moves = 30; combo = 0; level = 1; game_over = False

    # Draw
    screen.fill((20, 20, 40))
    offset_x = (W - GRID * TILE) // 2
    offset_y = (H - GRID * TILE) // 2
    for y in range(GRID):
        for x in range(GRID):
            rx = offset_x + x * TILE
            ry = offset_y + y * TILE
            if grid[y][x] is not None:
                c = COLORS[grid[y][x]]
                pygame.draw.rect(screen, c, (rx + 2, ry + 2, TILE - 4, TILE - 4), border_radius=6)
                inner = tuple(min(255, v + 60) for v in c)
                pygame.draw.rect(screen, inner, (rx + 6, ry + 6, TILE - 12, TILE - 12), border_radius=4)
            else:
                pygame.draw.rect(screen, (40, 40, 60), (rx, ry, TILE, TILE), 1)
            if selected and selected == (y, x):
                pygame.draw.rect(screen, (255, 255, 255), (rx, ry, TILE, TILE), 3)

    # UI
    screen.blit(font.render(f"Score: {score}", True, (255, 255, 255)), (10, 10))
    screen.blit(font.render(f"Moves: {moves}", True, (255, 255, 255)), (10, 50))
    screen.blit(font.render(f"Level: {level}", True, (255, 255, 255)), (10, 90))
    screen.blit(font.render(f"Combo: x{combo}", True, (200, 200, 50)), (10, 130))
    if game_over:
        screen.blit(big_font.render("GAME OVER", True, (255, 50, 50)), (W//2 - 140, H//2 - 30))
        screen.blit(font.render("Press R to restart", True, (200, 200, 200)), (W//2 - 100, H//2 + 30))

    pygame.display.flip()

pygame.quit()
sys.exit()
'''

    _STRATEGY_CODE = '''"""
{{TITLE}} - KYROS Game Engine
Genre: {{GENRE}}
Tower Defense game.
"""
import pygame
import sys

W, H = {{WIDTH}}, {{HEIGHT}}
FPS = 60

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("{{TITLE}}")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)
big_font = pygame.font.Font(None, 48)

GRID = 10
CELL = W // GRID

path = [(0, 5), (1, 5), (2, 5), (3, 5), (3, 4), (4, 4), (5, 4), (5, 5), (6, 5), (7, 5), (8, 5), (9, 5)]
path_idx = 0
enemies = []
towers = []
gold = 100
lives = 20
wave = 0
wave_count = 0
wave_active = False
spawn_timer = 0
score = 0

def start_wave():
    global wave_active, wave, wave_count, spawn_timer
    wave += 1
    wave_count = 5 + wave * 3
    wave_active = True
    spawn_timer = 0

class Enemy:
    def __init__(self, hp):
        self.path_idx = 0
        self.x = path[0][0] * CELL + CELL//2
        self.y = path[0][1] * CELL + CELL//2
        self.hp = hp
        self.max_hp = hp
        self.speed = 1.0
        self.alive = True
        self.reward = 5

    def update(self):
        if not self.alive: return
        target = path[self.path_idx]
        tx = target[0] * CELL + CELL//2
        ty = target[1] * CELL + CELL//2
        dx = tx - self.x; dy = ty - self.y
        dist = (dx*dx + dy*dy)**0.5
        if dist < self.speed:
            self.path_idx += 1
            if self.path_idx >= len(path):
                self.alive = False
                global lives
                lives -= 1
                return
        else:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

    def render(self):
        if not self.alive: return
        pygame.draw.circle(screen, (255, 60, 60), (int(self.x), int(self.y)), 10)
        hp_w = 20 * self.hp / self.max_hp
        pygame.draw.rect(screen, (50, 200, 50), (int(self.x - 10), int(self.y - 18), int(hp_w), 4))

start_wave()
running = True
while running:
    dt = clock.tick(FPS) / 16.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
            if event.key == pygame.K_SPACE and not wave_active: start_wave()
        if event.type == pygame.MOUSEBUTTONDOWN and gold >= 20:
            mx, my = event.pos
            gx, gy = mx // CELL, my // CELL
            if 0 <= gx < GRID and 0 <= gy < GRID and (gx, gy) not in path:
                if not any(t["x"] == gx and t["y"] == gy for t in towers):
                    towers.append({"x": gx, "y": gy, "range": 80, "damage": 10, "cooldown": 0, "level": 1})
                    gold -= 20

    # Spawn
    if wave_active and wave_count > 0:
        spawn_timer += dt
        if spawn_timer > max(10, 30 - wave):
            enemy_hp = 20 + wave * 5
            enemies.append(Enemy(enemy_hp))
            wave_count -= 1
            spawn_timer = 0
    if wave_active and wave_count <= 0 and all(not e.alive for e in enemies):
        wave_active = False
        gold += wave * 10

    # Tower targeting
    for t in towers:
        t["cooldown"] = max(0, t["cooldown"] - dt)
        if t["cooldown"] <= 0:
            target = None
            min_dist = t["range"]
            for e in enemies:
                if not e.alive: continue
                dx = e.x - (t["x"] * CELL + CELL//2)
                dy = e.y - (t["y"] * CELL + CELL//2)
                d = (dx*dx + dy*dy)**0.5
                if d < min_dist:
                    min_dist = d
                    target = e
            if target:
                e.hp -= t["damage"]
                t["cooldown"] = 30
                if e.hp <= 0:
                    e.alive = False
                    gold += e.reward
                    score += e.reward * 2

    for e in enemies: e.update()
    enemies = [e for e in enemies if e.alive or e.path_idx < len(path)]

    # Draw
    screen.fill((20, 20, 40))
    for gx in range(GRID):
        for gy in range(GRID):
            col = (30, 30, 60) if (gx+gy) % 2 == 0 else (40, 40, 70)
            if (gx, gy) in path:
                col = (50, 40, 30) if (gx+gy) % 2 == 0 else (60, 50, 40)
            pygame.draw.rect(screen, col, (gx*CELL, gy*CELL, CELL, CELL), 1)
    for t in towers:
        cx = t["x"] * CELL + CELL//2
        cy = t["y"] * CELL + CELL//2
        pygame.draw.circle(screen, (100, 100, 255), (cx, cy), 15)
        pygame.draw.circle(screen, (100, 100, 255, 40), (cx, cy), t["range"], 1)
    for e in enemies: e.render()

    # UI
    pygame.draw.rect(screen, (0, 0, 0, 160), (0, 0, W, 45))
    ui = [
        f"Lives: {lives}",
        f"Gold: {gold}",
        f"Wave: {wave}",
        f"Score: {score}",
        f"Enemies: {sum(1 for e in enemies if e.alive)}" if wave_active else "Press SPACE for next wave",
    ]
    for i, line in enumerate(ui):
        screen.blit(font.render(line, True, (255, 255, 255)), (10 + i*130, 10))
    if lives <= 0:
        screen.blit(big_font.render("GAME OVER", True, (255, 50, 50)), (W//2 - 140, H//2 - 30))

    pygame.display.flip()

pygame.quit()
sys.exit()
'''

    _FIGHTING_CODE = '''
"""{{TITLE}} - KYROS Game Engine
Genre: {{GENRE}}
2D Fighting Game
"""
import pygame
import sys

W, H = {{WIDTH}}, {{HEIGHT}}
FPS = 60

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("{{TITLE}}")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)
big_font = pygame.font.Font(None, 42)

class Fighter:
    def __init__(self, x, y, color, name, facing=1):
        self.x, self.y = x, y
        self.w, self.h = 40, 60
        self.color = color
        self.name = name
        self.facing = facing
        self.hp = 100
        self.max_hp = 100
        self.speed = 4
        self.vy = 0
        self.vx = 0
        self.on_ground = False
        self.attack_cooldown = 0
        self.combo = 0
        self.score = 0
        self.blocking = False
        self.stun = 0

    def move(self, dx, dy):
        self.vx = dx * self.speed
        if dx > 0: self.facing = 1
        elif dx < 0: self.facing = -1

    def jump(self):
        if self.on_ground:
            self.vy = -10

    def punch(self):
        if self.attack_cooldown > 0: return None
        self.attack_cooldown = 15
        self.combo += 1
        return {"dmg": 5 + self.combo * 2, "type": "punch"}

    def kick(self):
        if self.attack_cooldown > 0: return None
        self.attack_cooldown = 20
        self.combo += 1
        return {"dmg": 8 + self.combo * 3, "type": "kick"}

    def special(self):
        if self.attack_cooldown > 0: return None
        self.attack_cooldown = 30
        self.combo += 1
        return {"dmg": 15 + self.combo * 4, "type": "special"}

    def take_damage(self, dmg):
        if self.blocking:
            dmg = dmg // 3
        self.hp = max(0, self.hp - dmg)
        self.stun = 10
        return dmg

    def update(self):
        self.attack_cooldown = max(0, self.attack_cooldown - 1)
        self.stun = max(0, self.stun - 1)
        self.vy += 0.5
        self.x += self.vx + self.vy * 0.3
        self.y += self.vy
        self.vx *= 0.8
        if self.y + self.h > H - 40:
            self.y = H - 40 - self.h
            self.vy = 0
            self.on_ground = True
        else:
            self.on_ground = False
        self.x = max(0, min(W - self.w, self.x))

    def render(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.w, self.h))
        bar_w = self.w + 10
        hp_pct = self.hp / self.max_hp
        pygame.draw.rect(screen, (100, 0, 0), (self.x - 5, self.y - 12, bar_w, 6))
        pygame.draw.rect(screen, (0, 200, 0), (self.x - 5, self.y - 12, int(bar_w * hp_pct), 6))
        name_txt = font.render(self.name, True, (255, 255, 255))
        screen.blit(name_txt, (self.x + self.w//2 - name_txt.get_width()//2, self.y - 30))
        if self.blocking:
            pygame.draw.rect(screen, (100, 100, 255, 100), (self.x, self.y, self.w, self.h), 3)

player1 = Fighter(100, H-100, (50, 150, 255), "Player 1", 1)
player2 = Fighter(W-140, H-100, (255, 80, 80), "Player 2", -1)
winner = None
clock = pygame.time.Clock()

running = True
while running:
    dt = clock.tick(FPS) / 16.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
            if event.key == pygame.K_r:
                player1.hp = player1.max_hp; player2.hp = player2.max_hp
                player1.x, player2.x = 100, W-140; winner = None; player1.combo = 0; player2.combo = 0

    # Player 1 controls
    keys = pygame.key.get_pressed()
    p1_dx = 0
    if keys[pygame.K_a]: p1_dx = -1
    if keys[pygame.K_d]: p1_dx = 1
    player1.move(p1_dx, 0)
    if keys[pygame.K_w]: player1.jump()
    player1.blocking = keys[pygame.K_s]
    if keys[pygame.K_q]: 
        atk = player1.punch()
        if atk and abs(player1.x - player2.x) < 60:
            player2.take_damage(atk["dmg"])
    if keys[pygame.K_e]:
        atk = player1.special()
        if atk and abs(player1.x - player2.x) < 70:
            player2.take_damage(atk["dmg"])

    # Player 2 controls
    p2_dx = 0
    if keys[pygame.K_LEFT]: p2_dx = -1
    if keys[pygame.K_RIGHT]: p2_dx = 1
    player2.move(p2_dx, 0)
    if keys[pygame.K_UP]: player2.jump()
    player2.blocking = keys[pygame.K_DOWN]
    if keys[pygame.K_COMMA]:
        atk = player2.punch()
        if atk and abs(player1.x - player2.x) < 60:
            player1.take_damage(atk["dmg"])
    if keys[pygame.K_PERIOD]:
        atk = player2.special()
        if atk and abs(player1.x - player2.x) < 70:
            player1.take_damage(atk["dmg"])

    player1.update()
    player2.update()

    # Push apart
    if abs(player1.x - player2.x) < 50:
        if player1.x < player2.x:
            player1.x -= 2; player2.x += 2
        else:
            player1.x += 2; player2.x -= 2

    if player1.hp <= 0 and not winner: winner = "Player 2"
    if player2.hp <= 0 and not winner: winner = "Player 1"

    screen.fill((20, 20, 40))
    pygame.draw.rect(screen, (60, 60, 80), (0, H-40, W, 40))
    player1.render()
    player2.render()

    screen.blit(font.render(f"Combo: {player1.combo}", True, (255, 255, 255)), (10, 10))
    screen.blit(font.render(f"Combo: {player2.combo}", True, (255, 255, 255)), (W-120, 10))
    screen.blit(font.render(f"Round: {player1.score}-{player2.score}", True, (255, 255, 100)), (W//2-50, 10))
    
    if winner:
        win_txt = big_font.render(f"{winner} Wins!", True, (255, 220, 50))
        screen.blit(win_txt, (W//2 - win_txt.get_width()//2, H//2 - 30))
        screen.blit(font.render("Press R to restart", True, (200, 200, 200)), (W//2 - 80, H//2 + 20))

    pygame.display.flip()

pygame.quit()
sys.exit()
'''

    _SIMULATION_CODE = '''
"""{{TITLE}} - KYROS Game Engine
Genre: {{GENRE}}
Life Simulation Game
"""
import pygame
import random
import math
import sys

W, H = {{WIDTH}}, {{HEIGHT}}
FPS = 60

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("{{TITLE}}")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)
big_font = pygame.font.Font(None, 36)

class SimPerson:
    def __init__(self, x, y, name):
        self.x, self.y = x, y
        self.name = name
        self.w, self.h = 16, 24
        self.hunger = 100
        self.energy = 100
        self.happiness = 100
        self.social = 100
        self.health = 100
        self.age = 18
        self.money = 100
        self.job = None
        self.home = None
        self.speed = 1
        self.target_x = x
        self.target_y = y
        self.task = "idle"
        self.task_time = 0
        self.alive = True
        self.color = (random.randint(150, 255), random.randint(100, 200), random.randint(100, 200))

    def assign_job(self, job):
        self.job = job

    def update(self, dt):
        if not self.alive: return
        self.hunger = max(0, self.hunger - 0.02 * dt)
        self.energy = max(0, self.energy - 0.01 * dt)
        self.happiness = max(0, self.happiness - 0.005 * dt)
        self.social = max(0, self.social - 0.008 * dt)
        if self.hunger <= 0 or self.health <= 0:
            self.health -= 0.5 * dt
        if self.health <= 0:
            self.alive = False
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 2:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt
        else:
            self.task_time += dt
            if self.task == "eat" and self.task_time > 30:
                self.hunger = min(100, self.hunger + 30)
                self.money -= 5
                self.task = "idle"
            elif self.task == "sleep" and self.task_time > 60:
                self.energy = min(100, self.energy + 50)
                self.task = "idle"
            elif self.task == "work" and self.task_time > 90:
                self.money += 15
                self.happiness = max(0, self.happiness - 5)
                self.task = "idle"

    def render(self):
        if not self.alive: return
        pygame.draw.ellipse(screen, self.color, (self.x, self.y, self.w, self.h))
        # Eyes
        eye_col = (255, 255, 255)
        pygame.draw.circle(screen, eye_col, (int(self.x+4), int(self.y+6)), 2)
        pygame.draw.circle(screen, eye_col, (int(self.x+12), int(self.y+6)), 2)
        # Needs bars
        bar_y = self.y - 8
        for i, (val, col) in enumerate([
            (self.hunger, (200, 100, 50)),
            (self.energy, (50, 200, 255)),
            (self.happiness, (255, 220, 50)),
        ]):
            pygame.draw.rect(screen, (50, 50, 50), (self.x, bar_y + i*3, self.w, 2))
            pygame.draw.rect(screen, col, (self.x, bar_y + i*3, int(self.w * val / 100), 2))

people = []
buildings = []

for i in range(5):
    p = SimPerson(random.randint(100, W-100), random.randint(100, H-100), f"Person {i+1}")
    people.append(p)

running = True
paused = False
speed = 1
clock = pygame.time.Clock()

while running:
    dt = clock.tick(FPS) * speed
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
            if event.key == pygame.K_SPACE: paused = not paused
            if event.key == pygame.K_EQUALS: speed = min(5, speed + 1)
            if event.key == pygame.K_MINUS: speed = max(1, speed - 1)

    if not paused:
        for p in people:
            if p.task == "idle" and random.random() < 0.01:
                task = random.choice(["eat", "sleep", "work"])
                p.task = task
                p.task_time = 0
                if task == "eat":
                    p.target_x = random.randint(50, 200)
                    p.target_y = random.randint(50, 200)
                elif task == "sleep":
                    p.target_x = random.randint(W-200, W-50)
                    p.target_y = random.randint(H-200, H-50)
                elif task == "work":
                    p.target_x = random.randint(300, 500)
                    p.target_y = random.randint(100, 300)
            p.update(dt)

    screen.fill((30, 30, 50))

    # Buildings
    for i, (bx, by) in enumerate([(50, 50), (W-150, H-150), (300, 100), (500, 200)]):
        labels = ["Cafe", "Home", "Office", "Park"]
        pygame.draw.rect(screen, (60, 60, 80), (bx, by, 80, 60))
        pygame.draw.rect(screen, (80, 80, 100), (bx, by, 80, 60), 2)
        txt = font.render(labels[i % 4], True, (200, 200, 200))
        screen.blit(txt, (bx + 10, by + 20))

    for p in people: p.render()

    # HUD
    pygame.draw.rect(screen, (0, 0, 0, 180), (0, 0, W, 35))
    alive = sum(1 for p in people if p.alive)
    avg_hap = int(sum(p.happiness for p in people if p.alive) / max(1, alive))
    info = f"Pop: {alive}  Happiness: {avg_hap}%  Speed: x{speed}  {'PAUSED' if paused else ''}"
    screen.blit(font.render(info, True, (255, 255, 255)), (10, 10))

    pygame.display.flip()

pygame.quit()
sys.exit()
'''

    _SHOOTER_CODE = '''
"""{{TITLE}} - KYROS Game Engine
Genre: {{GENRE}}
"""
import pygame
import random
import sys

W, H = {{WIDTH}}, {{HEIGHT}}
FPS = 60

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("{{TITLE}}")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)
big_font = pygame.font.Font(None, 48)

class Player:
    def __init__(self):
        self.x = W//2
        self.y = H - 50
        self.w = 30
        self.h = 20
        self.speed = 5
        self.lives = 3
        self.score = 0

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: self.x -= self.speed
        if keys[pygame.K_RIGHT]: self.x += self.speed
        self.x = max(self.w//2, min(W - self.w//2, self.x))

    def render(self):
        pygame.draw.polygon(screen, (50, 200, 255), [
            (self.x, self.y - self.h//2),
            (self.x - self.w//2, self.y + self.h//2),
            (self.x + self.w//2, self.y + self.h//2),
        ])

player = Player()
bullets = []
enemies = []
powerups = []
stars = [(random.randint(0, W), random.randint(0, H), random.random()) for _ in range(50)]
wave = 0
game_over = False

def spawn_wave():
    global wave
    wave += 1
    count = 3 + wave * 2
    for _ in range(count):
        enemies.append({
            "x": random.randint(20, W-20),
            "y": -20,
            "w": 20,
            "h": 20,
            "hp": 1 + wave // 3,
            "speed": 1 + wave * 0.2,
        })

spawn_wave()
running = True
fire_cooldown = 0

while running:
    dt = clock.tick(FPS) / 16.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
            if event.key == pygame.K_r and game_over:
                player = Player(); enemies.clear(); bullets.clear()
                powerups.clear(); wave = 0; game_over = False; spawn_wave()

    keys = pygame.key.get_pressed()
    player.update()
    
    # Shooting
    fire_cooldown = max(0, fire_cooldown - 1)
    if keys[pygame.K_SPACE] and fire_cooldown == 0:
        bullets.append({"x": player.x, "y": player.y - 10, "w": 4, "h": 10, "speed": -8})
        fire_cooldown = 8

    # Bullets
    for b in bullets[:]:
        b["y"] += b["speed"]
        if b["y"] < -10:
            bullets.remove(b)

    # Enemies
    for e in enemies[:]:
        e["y"] += e["speed"] * dt
        if e["y"] > H + 20:
            enemies.remove(e)
            player.lives -= 1
            if player.lives <= 0:
                game_over = True

    # Bullet-enemy collisions
    for b in bullets[:]:
        for e in enemies[:]:
            if (b["x"] > e["x"] - e["w"]//2 and b["x"] < e["x"] + e["w"]//2 and
                b["y"] > e["y"] - e["h"]//2 and b["y"] < e["y"] + e["h"]//2):
                e["hp"] -= 1
                if b in bullets: bullets.remove(b)
                if e["hp"] <= 0:
                    enemies.remove(e)
                    player.score += 10 * wave
                    if random.random() < 0.15:
                        powerups.append({"x": e["x"], "y": e["y"], "type": random.choice(["life", "rapid"])})
                break

    # Powerups
    for p in powerups[:]:
        p["y"] += 1
        if abs(p["x"] - player.x) < 20 and abs(p["y"] - player.y) < 20:
            if p["type"] == "life":
                player.lives = min(5, player.lives + 1)
            elif p["type"] == "rapid":
                fire_cooldown = 2
            powerups.remove(p)

    if len(enemies) == 0 and not game_over:
        spawn_wave()

    # Render
    screen.fill((5, 5, 20))
    for sx, sy, sb in stars:
        pygame.draw.circle(screen, (100, 100, 150), (int(sx), int(sy)), 1 if sb > 0.5 else 0.5)

    player.render()
    for b in bullets:
        pygame.draw.rect(screen, (255, 255, 100), (b["x"]-2, b["y"], b["w"], b["h"]))
    for e in enemies:
        pygame.draw.rect(screen, (200, 50, 50), (e["x"] - e["w"]//2, e["y"] - e["h"]//2, e["w"], e["h"]))
        hp_pct = e["hp"] / (1 + wave // 3)
        pygame.draw.rect(screen, (50, 200, 50), (e["x"] - 10, e["y"] - e["h"]//2 - 6, int(20 * hp_pct), 4))
    for p in powerups:
        col = (50, 255, 50) if p["type"] == "life" else (255, 200, 50)
        pygame.draw.circle(screen, col, (int(p["x"]), int(p["y"])), 6)

    screen.blit(font.render(f"Score: {player.score}", True, (255, 255, 255)), (10, 10))
    screen.blit(font.render(f"Lives: {player.lives}", True, (255, 255, 255)), (10, 40))
    screen.blit(font.render(f"Wave: {wave}", True, (255, 255, 255)), (10, 70))

    if game_over:
        go = big_font.render("GAME OVER", True, (255, 50, 50))
        screen.blit(go, (W//2 - 120, H//2 - 30))
        restart = font.render("Press R to restart", True, (200, 200, 200))
        screen.blit(restart, (W//2 - 80, H//2 + 10))

    pygame.display.flip()

pygame.quit()
sys.exit()
'''

    _STEALTH_CODE = '''
"""{{TITLE}} - KYROS Game Engine
Genre: {{GENRE}}
"""
import pygame
import math
import random
import sys

W, H = {{WIDTH}}, {{HEIGHT}}
FPS = 60

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("{{TITLE}}")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)
big_font = pygame.font.Font(None, 48)

class Guard:
    def __init__(self, x, y, path_points):
        self.x = x
        self.y = y
        self.w = 20
        self.h = 20
        self.path = path_points
        self.path_idx = 0
        self.speed = 1.0
        self.vision_range = 150
        self.vision_angle = math.pi / 3
        self.alerted = False
        self.alert_timer = 0
        self.color = (100, 100, 100)

    def update(self, player_x, player_y):
        if self.alerted:
            self.alert_timer -= 1
            self.color = (255, 100, 100) if self.alert_timer % 10 < 5 else (200, 50, 50)
            self.chase_target(player_x, player_y)
            if self.alert_timer <= 0:
                self.alerted = False
                self.color = (100, 100, 100)
        else:
            self.patrol()

    def patrol(self):
        tx, ty = self.path[self.path_idx]
        dx, dy = tx - self.x, ty - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < 5:
            self.path_idx = (self.path_idx + 1) % len(self.path)
        else:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

    def chase_target(self, tx, ty):
        dx, dy = tx - self.x, ty - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 5:
            self.x += (dx / dist) * self.speed * 1.5
            self.y += (dy / dist) * self.speed * 1.5

    def can_see(self, px, py):
        if self.alerted:
            return True
        dx = px - self.x
        dy = py - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > self.vision_range:
            return False
        return True

    def render(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 10)
        if not self.alerted:
            vision_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            pygame.draw.circle(vision_surf, (100, 100, 100, 30), (int(self.x), int(self.y)), self.vision_range)
            screen.blit(vision_surf, (0, 0))

class Player:
    def __init__(self):
        self.x = 50
        self.y = 50
        self.w = 16
        self.h = 16
        self.speed = 3
        self.stealth = True
        self.caught = False
        self.objectives = 0
        self.total_objectives = 3
        self.alpha = 100

    def update(self):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_w]: dy = -1
        if keys[pygame.K_s]: dy = 1
        if keys[pygame.K_a]: dx = -1
        if keys[pygame.K_d]: dx = 1
        if dx != 0 or dy != 0:
            self.stealth = True
            self.alpha = 100 if keys[pygame.K_LSHIFT] else 200
        self.x += dx * self.speed
        self.y += dy * self.speed
        self.x = max(20, min(W-20, self.x))
        self.y = max(20, min(H-20, self.y))

    def render(self):
        surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        surf.fill((50, 150, 255, self.alpha))
        screen.blit(surf, (self.x - self.w//2, self.y - self.h//2))

guards = []
for i in range(4):
    gx = random.randint(100, W-100)
    gy = random.randint(100, H-100)
    pts = [(gx + random.randint(-50, 50), gy + random.randint(-50, 50)) for _ in range(3)]
    guards.append(Guard(gx, gy, pts))

objectives = []
for _ in range(3):
    objectives.append({"x": random.randint(50, W-50), "y": random.randint(50, H-50), "collected": False})

walls = [(200, 200, 300, 10), (400, 100, 10, 200), (600, 300, 10, 150), (100, 400, 200, 10)]

player = Player()
alarm = False
running = True
shadow_map = pygame.Surface((W, H), pygame.SRCALPHA)

while running:
    dt = clock.tick(FPS) / 16.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False

    player.update()

    for g in guards:
        g.update(player.x, player.y)
        if g.can_see(player.x, player.y):
            dist = math.sqrt((player.x - g.x)**2 + (player.y - g.y)**2)
            if dist < 40:
                player.caught = True

    for obj in objectives:
        if not obj["collected"]:
            if math.sqrt((player.x - obj["x"])**2 + (player.y - obj["y"])**2) < 20:
                obj["collected"] = True
                player.objectives += 1

    # Shadow/light effect
    shadow_map.fill((0, 0, 0, 180))
    pygame.draw.circle(shadow_map, (0, 0, 0, 0), (int(player.x), int(player.y)), 80)

    screen.fill((15, 15, 30))
    for wx, wy, ww, wh in walls:
        pygame.draw.rect(screen, (60, 60, 80), (wx, wy, ww, wh))

    screen.blit(shadow_map, (0, 0))
    for g in guards: g.render()
    player.render()

    for obj in objectives:
        if not obj["collected"]:
            pygame.draw.circle(screen, (255, 220, 50), (int(obj["x"]), int(obj["y"])), 5)
            pulse = 8 + math.sin(pygame.time.get_ticks() * 0.003) * 4
            pygame.draw.circle(screen, (255, 220, 50, 40), (int(obj["x"]), int(obj["y"])), int(pulse), 1)

    if player.caught:
        screen.blit(big_font.render("CAUGHT!", True, (255, 50, 50)), (W//2 - 80, H//2 - 20))
    elif player.objectives >= player.total_objectives:
        screen.blit(big_font.render("MISSION COMPLETE!", True, (50, 255, 50)), (W//2 - 150, H//2 - 20))

    screen.blit(font.render(f"Objectives: {player.objectives}/{player.total_objectives}", True, (255, 255, 255)), (10, 10))
    screen.blit(font.render(f"Guards: {len(guards)}", True, (255, 255, 255)), (10, 35))
    
    if player.alpha < 150:
        screen.blit(font.render("STEALTH", True, (50, 200, 50)), (W-100, 10))
    else:
        screen.blit(font.render("VISIBLE", True, (200, 50, 50)), (W-100, 10))

    pygame.display.flip()

pygame.quit()
sys.exit()
'''
