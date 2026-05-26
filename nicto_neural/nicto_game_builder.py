#!/usr/bin/env python3
"""
NICTO Real AI — 3D Raycasting FPS Game Builder
CPU-only standalone game generator. Produces a complete playable game.
"""
import json, os, sys, datetime, textwrap, random
from pathlib import Path

HERE = Path(__file__).parent
OUTPUT_DIR = HERE / "nicto_outputs" / "games"

GAME_TEMPLATES = {
    "fps": "First-person shooter with raycasting engine",
    "maze": "Maze exploration game",
    "dungeon": "Dungeon crawler with procedural rooms",
    "castle": "Castle siege game",
}


def generate_game_source(name: str, map_data: list, colors: dict, game_type: str = "fps") -> str:
    """Generate a complete, playable raycasting FPS game."""
    w, h = len(map_data[0]), len(map_data)
    color_str = json.dumps(colors)
    map_str = ",\n        ".join(str(row) for row in map_data)
    player_start = _find_player_start(map_data)

    return f'''#!/usr/bin/env python3
"""NICTO Generated Game: {name} — {game_type}"""
import pygame, math, sys
from pygame.locals import *

WIDTH, HEIGHT = 800, 600
FOV = math.pi / 3
HALF_FOV = FOV / 2
HALF_HEIGHT = HEIGHT // 2
PLAYER_SPEED = 0.05
ROT_SPEED = 0.03
MAP_W, MAP_H = {w}, {h}
COLORS = {color_str}
MAP = [
        {map_str}
    ]

def cast_ray(x, y, angle, max_dist=16.0):
    sin_a, cos_a = math.sin(angle), math.cos(angle)
    dist = 0.0
    while dist < max_dist:
        dist += 0.02
        mx, my = int(x + cos_a * dist), int(y + sin_a * dist)
        if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
            return max_dist, None
        cell = MAP[my][mx]
        if cell > 0:
            # Find exact wall side for texturing
            px, py = x + cos_a * dist, y + sin_a * dist
            wall_x = px - mx if (py - my) < 0.5 else 1.0 - (px - mx)
            return dist, (cell, wall_x)
    return max_dist, None

def draw_frame(screen, px, py, angle):
    screen.fill((20, 20, 30))
    # Floor and ceiling
    screen.fill((10, 10, 20), (0, 0, WIDTH, HALF_HEIGHT))
    screen.fill((30, 30, 40), (0, HALF_HEIGHT, WIDTH, HALF_HEIGHT))

    for col in range(WIDTH):
        ray_angle = angle - HALF_FOV + (col / WIDTH) * FOV
        dist, hit = cast_ray(px, py, ray_angle)
        if dist > 15.9:
            continue

        # Fix fisheye
        dist *= math.cos(ray_angle - angle)
        wall_h = min(HALF_HEIGHT / (dist + 0.001), HEIGHT)
        top = HALF_HEIGHT - wall_h // 2
        bot = HALF_HEIGHT + wall_h // 2

        # Shade by distance
        shade = max(30, min(255, int(255 - dist * 14)))
        if hit:
            cell_id, wx = hit
            color = COLORS.get(str(cell_id), (shade, shade, shade))
            shaded = tuple(max(0, min(255, int(c * shade / 255))) for c in color)
            pygame.draw.rect(screen, shaded, (col, int(top), 1, int(bot - top)))

    # Minimap
    mm_scale = 4
    ox, oy = WIDTH - MAP_W * mm_scale - 10, 10
    for my, row in enumerate(MAP):
        for mx, cell in enumerate(row):
            if cell > 0:
                ci = COLORS.get(str(cell), (100, 100, 100))
                pygame.draw.rect(screen, ci, (ox + mx * mm_scale, oy + my * mm_scale, mm_scale, mm_scale))
    # Player on minimap
    mx, my = int(px * mm_scale) + ox, int(py * mm_scale) + oy
    pygame.draw.circle(screen, (255, 50, 50), (mx, my), 3)
    # Direction
    dx, dy = math.cos(angle) * 8, math.sin(angle) * 8
    pygame.draw.line(screen, (255, 255, 50), (mx, my), (mx + dx, my + dy), 2)

    # Crosshair
    cx, cy = WIDTH // 2, HEIGHT // 2
    pygame.draw.line(screen, (255, 255, 255), (cx - 10, cy), (cx + 10, cy), 2)
    pygame.draw.line(screen, (255, 255, 255), (cx, cy - 10), (cx, cy + 10), 2)

    # Info
    font = pygame.font.Font(None, 24)
    fps_t = font.render(f"FPS: {{clock.get_fps():.0f}} | WASD move, Arrow turn", True, (180, 255, 180))
    screen.blit(fps_t, (10, HEIGHT - 30))

def main():
    global clock
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("NICTO Game: {name}")
    clock = pygame.time.Clock()

    px, py = {player_start["x"]:.2f}, {player_start["y"]:.2f}
    angle = 0.0

    running = True
    while running:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False

        keys = pygame.key.get_pressed()
        if keys[K_LEFT]:
            angle -= ROT_SPEED
        if keys[K_RIGHT]:
            angle += ROT_SPEED
        if keys[K_UP] or keys[K_w]:
            nx = px + math.cos(angle) * PLAYER_SPEED
            ny = py + math.sin(angle) * PLAYER_SPEED
            if 0 <= int(ny) < MAP_H and 0 <= int(nx) < MAP_W and MAP[int(ny)][int(nx)] == 0:
                px, py = nx, ny
        if keys[K_DOWN] or keys[K_s]:
            nx = px - math.cos(angle) * PLAYER_SPEED
            ny = py - math.sin(angle) * PLAYER_SPEED
            if 0 <= int(ny) < MAP_H and 0 <= int(nx) < MAP_W and MAP[int(ny)][int(nx)] == 0:
                px, py = nx, ny

        draw_frame(screen, px, py, angle)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
'''


def _find_player_start(map_data):
    for y, row in enumerate(map_data):
        for x, cell in enumerate(row):
            if cell == 0:
                return {"x": x + 0.5, "y": y + 0.5}
    return {"x": 1.5, "y": 1.5}


def _generate_maze(w: int, h: int) -> list:
    """Generate a maze using recursive backtracker."""
    # Start with all walls
    grid = [[1] * (w * 2 + 1) for _ in range(h * 2 + 1)]

    def carve(x, y):
        grid[y * 2 + 1][x * 2 + 1] = 0
        dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = x + dx * 2, y + dy * 2
            if 0 <= nx < w and 0 <= ny < h and grid[ny * 2 + 1][nx * 2 + 1] == 1:
                grid[y * 2 + 1 + dy][x * 2 + 1 + dx] = 0
                carve(nx, ny)

    carve(0, 0)

    # Convert to game map (0=empty, 1=wall)
    game_map = []
    for row in grid:
        game_map.append([1 if c == 1 else 0 for c in row])
    return game_map


def _generate_dungeon(w: int, h: int, rooms: int = 8) -> list:
    """Generate dungeon with rooms connected by corridors."""
    grid = [[1] * w for _ in range(h)]
    room_list = []
    for _ in range(rooms):
        rw, rh = random.randint(3, 7), random.randint(3, 7)
        rx, ry = random.randint(1, w - rw - 2), random.randint(1, h - rh - 2)
        # Check overlap
        ok = True
        for ox in range(rx - 1, rx + rw + 2):
            for oy in range(ry - 1, ry + rh + 2):
                if 0 <= ox < w and 0 <= oy < h and grid[oy][ox] == 0:
                    ok = False
        if not ok:
            continue
        for dx in range(rw):
            for dy in range(rh):
                grid[ry + dy][rx + dx] = 0
        room_list.append((rx + rw // 2, ry + rh // 2))
    # Connect rooms with L-shaped corridors
    for i in range(len(room_list) - 1):
        x1, y1 = room_list[i]
        x2, y2 = room_list[i + 1]
        for x in range(min(x1, x2), max(x1, x2) + 1):
            grid[y1][x] = 0
        for y in range(min(y1, y2), max(y1, y2) + 1):
            grid[y][x2] = 0
    return grid


class NICTOGameBuilder:
    def __init__(self):
        self.games_dir = OUTPUT_DIR
        self.games_dir.mkdir(parents=True, exist_ok=True)

    def build(self, name: str = None, game_type: str = "fps", map_size: tuple = (16, 16)) -> dict:
        if name is None:
            name = f"nicto_game_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Generate map
        if game_type == "maze":
            map_data = _generate_maze(map_size[0] // 2, map_size[1] // 2)
        elif game_type == "dungeon":
            map_data = _generate_dungeon(map_size[0], map_size[1], rooms=10)
        else:
            # Default map (simple rooms)
            map_data = [[1] * map_size[0] for _ in range(map_size[1])]
            for y in range(1, map_size[1] - 1):
                for x in range(1, map_size[0] - 1):
                    if random.random() < 0.3 and not (1 < x < map_size[0] - 2 and 1 < y < map_size[1] - 2 and random.random() < 0.5):
                        map_data[y][x] = 0

        # Generate player start
        start = _find_player_start(map_data)

        colors = {
            "1": (180, 60, 60), "2": (60, 120, 200), "3": (60, 180, 60),
            "4": (200, 180, 60), "5": (160, 60, 180), "6": (60, 180, 180),
        }

        source = generate_game_source(name, map_data, colors, game_type)

        game_path = self.games_dir / f"{name}.py"
        with open(game_path, "w") as f:
            f.write(source)

        return {
            "status": "completed",
            "name": name,
            "type": game_type,
            "path": str(game_path),
            "map_size": (len(map_data[0]), len(map_data)),
            "player_start": start,
            "instructions": "Run: python " + str(game_path),
        }

    def list_games(self) -> list:
        games = list(self.games_dir.glob("*.py"))
        return [{"name": g.stem, "path": str(g), "size_kb": round(g.stat().st_size / 1024, 1)} for g in games]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="NICTO Game Builder")
    parser.add_argument("--name", default=None, help="Game name")
    parser.add_argument("--type", choices=["fps", "maze", "dungeon"], default="fps", help="Game type")
    parser.add_argument("--width", type=int, default=16, help="Map width")
    parser.add_argument("--height", type=int, default=16, help="Map height")
    parser.add_argument("--list", action="store_true", help="List generated games")
    args = parser.parse_args()

    builder = NICTOGameBuilder()

    if args.list:
        games = builder.list_games()
        if games:
            print("Generated games:")
            for g in games:
                print(f"  {g['name']}: {g['size_kb']}KB — {g['path']}")
        else:
            print("No games generated yet.")
        return

    result = builder.build(name=args.name, game_type=args.type, map_size=(args.width, args.height))
    print(json.dumps(result, indent=2))
    print(f"\nTo play: python {result['path']}")


if __name__ == "__main__":
    main()
