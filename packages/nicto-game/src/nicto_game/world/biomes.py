"""Biome generation system for NICTO Omega Game Engine."""

from __future__ import annotations
import math
import random
from typing import Optional

from nicto_game.core.types import TileType, GameMap, Biome


class BiomeGenerator:
    """Generates heightmaps, moisture maps, and biome classifications."""

    def __init__(self, rng: random.Random):
        self.rng = rng
        self._perm: list[int] = []
        self._init_perlin()

    def _init_perlin(self):
        p = list(range(256))
        self.rng.shuffle(p)
        self._perm = p + p

    def _fade(self, t: float) -> float:
        return t * t * t * (t * (t * 6 - 15) + 10)

    def _lerp(self, a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    def _grad(self, hash_val: int, x: float, y: float) -> float:
        h = hash_val & 3
        return (x if h & 1 else -x) + (y if h & 2 else -y)

    def perlin(self, x: float, y: float) -> float:
        xi, yi = int(math.floor(x)) & 255, int(math.floor(y)) & 255
        xf, yf = x - math.floor(x), y - math.floor(y)
        u, v = self._fade(xf), self._fade(yf)
        aa = self._perm[xi] + yi
        ab = self._perm[xi] + yi + 1
        ba = self._perm[xi + 1] + yi
        bb = self._perm[xi + 1] + yi + 1
        return self._lerp(
            self._lerp(self._grad(self._perm[aa], xf, yf),
                       self._grad(self._perm[ba], xf - 1, yf), u),
            self._lerp(self._grad(self._perm[ab], xf, yf - 1),
                       self._grad(self._perm[bb], xf - 1, yf - 1), u),
            v,
        )

    def octave_noise(self, x: float, y: float, octaves: int = 4, persistence: float = 0.5) -> float:
        value, amplitude, frequency, max_val = 0.0, 1.0, 1.0, 0.0
        for _ in range(octaves):
            value += amplitude * self.perlin(x * frequency, y * frequency)
            max_val += amplitude
            amplitude *= persistence
            frequency *= 2
        return value / max_val

    def generate_heightmap(self, w: int, h: int, roughness: float = 0.5) -> list[list[float]]:
        scale = 6.0
        hm = [[0.0] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                nx = x / max(w, 1) * scale + self.rng.random() * 0.01
                ny = y / max(h, 1) * scale + self.rng.random() * 0.01
                val = self.octave_noise(nx, ny, octaves=6, persistence=roughness)
                hm[y][x] = (val + 1) / 2
        return hm

    def generate_moisture_map(self, w: int, h: int) -> list[list[float]]:
        scale = 8.0
        mm = [[0.0] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                nx = x / max(w, 1) * scale
                ny = y / max(h, 1) * scale
                val = self.octave_noise(nx, ny, octaves=3, persistence=0.4)
                mm[y][x] = (val + 1) / 2
        return mm

    def classify_biomes(self, heightmap: list[list[float]],
                        moisture: list[list[float]]) -> list[list[Biome]]:
        h, w = len(heightmap), len(heightmap[0])
        bm = [[Biome.PLAINS] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                elev = heightmap[y][x]
                moist = moisture[y][x]
                if elev < 0.15:
                    bm[y][x] = Biome.OCEAN
                elif elev < 0.25:
                    bm[y][x] = Biome.SWAMP if moist > 0.6 else Biome.PLAINS
                elif elev < 0.40:
                    if moist < 0.3:
                        bm[y][x] = Biome.DESERT
                    elif moist < 0.5:
                        bm[y][x] = Biome.SAVANNA
                    else:
                        bm[y][x] = Biome.FOREST
                elif elev < 0.55:
                    if moist < 0.3:
                        bm[y][x] = Biome.PLAINS
                    elif moist < 0.6:
                        bm[y][x] = Biome.FOREST
                    else:
                        bm[y][x] = Biome.JUNGLE
                elif elev < 0.70:
                    bm[y][x] = Biome.FOREST if moist > 0.5 else Biome.SAVANNA
                elif elev < 0.85:
                    bm[y][x] = Biome.MOUNTAINS
                else:
                    bm[y][x] = Biome.SNOW
        return bm

    def generate_rivers(self, gm: GameMap, heightmap: list[list[float]],
                        water_level: float):
        w, h = gm.width, gm.height
        num_rivers = max(1, (w * h) // 2000)

        for _ in range(num_rivers):
            attempts = 0
            while attempts < 50:
                sx = self.rng.randint(1, w - 2)
                sy = self.rng.randint(1, h - 2)
                if heightmap[sy][sx] > 0.5:
                    break
                attempts += 1
            else:
                continue

            x, y = sx, sy
            for _ in range(max(w, h) * 2):
                if not (0 <= x < w and 0 <= y < h):
                    break
                if heightmap[y][x] < water_level:
                    break
                if TileType(gm.tiles[y][x]) in (TileType.WALL, TileType.ROCK, TileType.BUILDING):
                    break
                gm.tiles[y][x] = TileType.WATER
                dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                lowest_dir = min(dirs, key=lambda d: (
                    heightmap[y + d[1]][x + d[0]]
                    if 0 <= y + d[1] < h and 0 <= x + d[0] < w
                    else float('inf')
                ))
                x += lowest_dir[0]
                y += lowest_dir[1]
