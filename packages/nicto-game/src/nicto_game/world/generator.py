from __future__ import annotations
import math
import random
from typing import Optional, Any

from nicto_game.core.config import GameConfig, GameGenre
from nicto_game.core.types import (
    TileType, TILE_COLORS, TILE_WALKABLE, GameMap, Biome,
)


class WorldGenerator:
    """AI World Generator — open worlds, terrain, biomes, ecosystems."""

    def __init__(self):
        self.rng = random.Random()

    async def generate(self, config: GameConfig) -> GameMap:
        self.rng = random.Random(config.world.seed or random.randint(0, 2 ** 31))
        w, h = max(config.world.width, 8), max(config.world.height, 8)

        if config.genre in (GameGenre.MAZE, GameGenre.ROGUELIKE):
            return self._generate_maze(w, h, config)
        elif config.genre == GameGenre.DUNGEON:
            return self._generate_dungeon(w, h, config)
        elif config.genre in (GameGenre.OPEN_WORLD, GameGenre.SURVIVAL,
                               GameGenre.RPG, GameGenre.SANDBOX):
            return self._generate_open_world(w, h, config)
        else:
            return self._generate_rooms(w, h, config)

    def _generate_maze(self, w: int, h: int, config: GameConfig) -> GameMap:
        grid = [[TileType.WALL] * w for _ in range(h)]
        start_x, start_y = 1, 1
        grid[start_y][start_x] = TileType.EMPTY
        stack = [(start_x, start_y)]

        while stack:
            cx, cy = stack[-1]
            neighbors = []
            for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                nx, ny = cx + dx, cy + dy
                if 0 < nx < w - 1 and 0 < ny < h - 1 and grid[ny][nx] == TileType.WALL:
                    neighbors.append((nx, ny, dx // 2, dy // 2))
            if neighbors:
                nx, ny, px, py = self.rng.choice(neighbors)
                grid[cy + py][cx + px] = TileType.EMPTY
                grid[ny][nx] = TileType.EMPTY
                stack.append((nx, ny))
            else:
                stack.pop()

        gm = GameMap(width=w, height=h, tiles=grid)
        self._place_features(gm, config)
        return gm

    def _generate_dungeon(self, w: int, h: int, config: GameConfig) -> GameMap:
        grid = [[TileType.WALL] * w for _ in range(h)]
        rooms = []
        num_rooms = max(4, (w * h) // 300)

        for _ in range(num_rooms * 3):
            rw = self.rng.randint(3, min(8, w - 4))
            rh = self.rng.randint(3, min(8, h - 4))
            rx = self.rng.randint(1, w - rw - 1)
            ry = self.rng.randint(1, h - rh - 1)
            overlap = any(
                rx < rx2 + rw2 + 1 and rx + rw + 1 > rx2 and
                ry < ry2 + rh2 + 1 and ry + rh + 1 > ry2
                for (rx2, ry2, rw2, rh2) in rooms
            )
            if not overlap:
                rooms.append((rx, ry, rw, rh))
                for y in range(ry, ry + rh):
                    for x in range(rx, rx + rw):
                        grid[y][x] = TileType.EMPTY

        if len(rooms) >= 2:
            for i in range(1, len(rooms)):
                x1, y1 = rooms[i - 1][0] + rooms[i - 1][2] // 2, rooms[i - 1][1] + rooms[i - 1][3] // 2
                x2, y2 = rooms[i][0] + rooms[i][2] // 2, rooms[i][1] + rooms[i][3] // 2
                if self.rng.choice([True, False]):
                    for x in range(min(x1, x2), max(x1, x2) + 1):
                        if 0 <= y1 < h:
                            grid[y1][x] = TileType.EMPTY
                    for y in range(min(y1, y2), max(y1, y2) + 1):
                        if 0 <= x2 < w:
                            grid[y][x2] = TileType.EMPTY
                else:
                    for y in range(min(y1, y2), max(y1, y2) + 1):
                        if 0 <= x1 < w:
                            grid[y][x1] = TileType.EMPTY
                    for x in range(min(x1, x2), max(x1, x2) + 1):
                        if 0 <= y2 < h:
                            grid[y2][x] = TileType.EMPTY

        # Place doors on some room edges
        for rx, ry, rw, rh in rooms:
            if self.rng.random() < 0.4:
                door_x = rx + self.rng.randint(0, rw - 1)
                door_y = ry + rh
                if 0 <= door_y < h and grid[door_y][door_x] == TileType.EMPTY:
                    grid[door_y - 1][door_x] = TileType.DOOR

        gm = GameMap(width=w, height=h, tiles=grid)
        self._place_features(gm, config)
        return gm

    def _generate_rooms(self, w: int, h: int, config: GameConfig) -> GameMap:
        grid = [[TileType.WALL] * w for _ in range(h)]
        rooms = []
        num_rooms = max(3, (w * h) // 200)

        for _ in range(num_rooms * 2):
            rw = self.rng.randint(3, min(10, w - 4))
            rh = self.rng.randint(3, min(8, h - 4))
            rx = self.rng.randint(1, w - rw - 1)
            ry = self.rng.randint(1, h - rh - 1)
            overlap = any(
                rx < rx2 + rw2 + 1 and rx + rw + 1 > rx2 and
                ry < ry2 + rh2 + 1 and ry + rh + 1 > ry2
                for (rx2, ry2, rw2, rh2) in rooms
            )
            if not overlap:
                rooms.append((rx, ry, rw, rh))
                walls = 0.8
                for y in range(ry, ry + rh):
                    for x in range(rx, rx + rw):
                        if (y == ry or y == ry + rh - 1 or
                            x == rx or x == rx + rw - 1):
                            if self.rng.random() < walls:
                                grid[y][x] = TileType.WALL
                            else:
                                grid[y][x] = TileType.EMPTY
                        else:
                            grid[y][x] = TileType.EMPTY

        if len(rooms) >= 2:
            for i in range(1, len(rooms)):
                cx1 = rooms[i - 1][0] + rooms[i - 1][2] // 2
                cy1 = rooms[i - 1][1] + rooms[i - 1][3] // 2
                cx2 = rooms[i][0] + rooms[i][2] // 2
                cy2 = rooms[i][1] + rooms[i][3] // 2
                for x in range(min(cx1, cx2), max(cx1, cx2) + 1):
                    if 0 <= cy1 < h:
                        grid[cy1][x] = TileType.EMPTY
                for y in range(min(cy1, cy2), max(cy1, cy2) + 1):
                    if 0 <= cx2 < w:
                        grid[y][cx2] = TileType.EMPTY

        gm = GameMap(width=w, height=h, tiles=grid)
        self._place_features(gm, config)
        return gm

    def _generate_open_world(self, w: int, h: int, config: GameConfig) -> GameMap:
        from nicto_game.world.biomes import BiomeGenerator
        bg = BiomeGenerator(self.rng)

        hm = bg.generate_heightmap(w, h, config.world.mountain_roughness)

        moisture = bg.generate_moisture_map(w, h)
        biome_map = bg.classify_biomes(hm, moisture)

        grid = [[TileType.EMPTY] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                elev = hm[y][x]
                bm = biome_map[y][x]
                if elev < config.world.water_level:
                    grid[y][x] = TileType.WATER
                elif bm == Biome.OCEAN:
                    grid[y][x] = TileType.WATER
                elif bm in (Biome.DESERT, Biome.SAVANNA):
                    grid[y][x] = TileType.SAND
                elif bm == Biome.SNOW:
                    grid[y][x] = TileType.SNOW
                elif bm == Biome.MOUNTAINS:
                    grid[y][x] = TileType.ROCK if elev > 0.65 else TileType.WALL
                elif bm in (Biome.FOREST, Biome.JUNGLE) and elev > config.world.water_level + 0.05:
                    grid[y][x] = TileType.TREE if self.rng.random() < config.world.tree_density else TileType.EMPTY
                elif bm == Biome.SWAMP and elev > config.world.water_level + 0.02:
                    grid[y][x] = TileType.WATER if self.rng.random() < 0.3 else TileType.TREE
                elif elev > 0.55:
                    grid[y][x] = TileType.ROCK if self.rng.random() < 0.15 else TileType.EMPTY

        gm = GameMap(width=w, height=h, tiles=grid, heightmap=hm)
        gm.properties["biome_map"] = biome_map

        if config.world.rivers:
            bg.generate_rivers(gm, hm, config.world.water_level)
        if config.world.roads and config.world.villages > 0:
            self._generate_roads(gm)
        if config.world.buildings:
            self._generate_villages(gm, config.world.villages, config)

        self._place_features(gm, config)
        return gm

    def _generate_roads(self, gm: GameMap):
        w, h = gm.width, gm.height
        for y in range(1, h - 1, self.rng.randint(8, 16)):
            for x in range(w):
                if gm.tiles[y][x] in (TileType.EMPTY, TileType.SAND):
                    gm.tiles[y][x] = TileType.ROAD

    def _generate_villages(self, gm: GameMap, count: int, config: GameConfig):
        for _ in range(count):
            for attempt in range(20):
                vx = self.rng.randint(4, gm.width - 5)
                vy = self.rng.randint(4, gm.height - 5)
                if gm.tiles[vy][vx] in (TileType.EMPTY, TileType.SAND, TileType.ROAD):
                    for by in range(-2, 3):
                        for bx in range(-2, 3):
                            ny, nx = vy + by, vx + bx
                            if 0 <= ny < gm.height and 0 <= nx < gm.width:
                                if abs(bx) <= 1 and abs(by) <= 1:
                                    gm.tiles[ny][nx] = TileType.BUILDING
                                else:
                                    gm.tiles[ny][nx] = TileType.ROAD
                    gm.spawn_points[f"village_{_}"] = (vx, vy)
                    break

    def _place_features(self, gm: GameMap, config: GameConfig):
        w, h = gm.width, gm.height
        empties = [(x, y) for y in range(h) for x in range(w)
                    if TileType(gm.tiles[y][x]) in TILE_WALKABLE]

        if not empties:
            return

        self.rng.shuffle(empties)

        player_pos = empties.pop(0) if empties else (1, 1)
        gm.spawn_points["player"] = player_pos

        exit_pos = empties.pop() if empties else (w - 2, h - 2)
        gm.tiles[exit_pos[1]][exit_pos[0]] = TileType.EXIT
        gm.spawn_points["exit"] = exit_pos

        for i in range(min(config.world.enemies, len(empties))):
            ex, ey = empties[i]
            gm.tiles[ey][ex] = TileType.ENEMY_SPAWN
            gm.spawn_points[f"enemy_{i}"] = (ex, ey)

        offset = config.world.enemies
        for i in range(min(config.world.npcs, len(empties) - offset)):
            if offset + i < len(empties):
                nx, ny = empties[offset + i]
                gm.tiles[ny][nx] = TileType.NPC_SPAWN
                gm.spawn_points[f"npc_{i}"] = (nx, ny)

        for i in range(min(3, len(empties) - offset - config.world.npcs)):
            idx = offset + config.world.npcs + i
            if idx < len(empties):
                ix, iy = empties[idx]
                gm.tiles[iy][ix] = TileType.ITEM
                gm.spawn_points[f"item_{i}"] = (ix, iy)

        if config.world.buildings and config.genre in (GameGenre.RPG, GameGenre.ADVENTURE):
            for _ in range(min(3, len(empties) - offset - config.world.npcs - 5)):
                idx = self.rng.randint(0, len(empties) - 1)
                bx, by = empties[idx]
                gm.tiles[by][bx] = TileType.CHEST
