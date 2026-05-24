"""Procedural content generation for NIKTO Game Engine.

Terrain generation (Perlin noise), dungeon layouts, quest generation, loot tables.
"""
import math
import random
import hashlib


class NoiseGenerator:
    def __init__(self, seed=42):
        self.seed = seed
        random.seed(seed)

    def perlin_noise(self, x, y, scale=0.1, octaves=4, persistence=0.5):
        value = 0.0
        amplitude = 1.0
        frequency = scale
        max_value = 0.0
        for _ in range(octaves):
            value += self._noise_2d(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= 2.0
        return value / max_value

    def _noise_2d(self, x, y):
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255
        xf = x - math.floor(x)
        yf = y - math.floor(y)
        u = xf * xf * (3.0 - 2.0 * xf)
        v = yf * yf * (3.0 - 2.0 * yf)
        aa = self._p(self._p(xi) + yi)
        ab = self._p(self._p(xi) + yi + 1)
        ba = self._p(self._p(xi + 1) + yi)
        bb = self._p(self._p(xi + 1) + yi + 1)
        x1 = self._lerp(self._grad(aa, xf, yf), self._grad(ba, xf - 1, yf), u)
        x2 = self._lerp(self._grad(ab, xf, yf - 1), self._grad(bb, xf - 1, yf - 1), u)
        return self._lerp(x1, x2, v)

    def _p(self, idx):
        return self._perm[idx & 255]

    def _grad(self, hash_code, x, y):
        h = hash_code & 3
        u = x if h & 1 == 0 else -x
        v = y if h & 2 == 0 else -y
        return u + v

    def _lerp(self, a, b, t):
        return a + t * (b - a)

    def _hash_bytes(self, b):
        return int(hashlib.sha256(b).hexdigest()[:8], 16) % 256

    def __init_permutation(self):
        perm = list(range(256))
        random.shuffle(perm)
        perm += perm
        return perm

    def __getattr__(self, name):
        if name == "_perm" and not hasattr(self, "_perm_initialized"):
            self._perm = self.__init_permutation()
            self._perm_initialized = True
            return self._perm
        raise AttributeError(name)


class TerrainGenerator:
    def __init__(self, width=64, height=64, seed=42):
        self.width = width
        self.height = height
        self.noise = NoiseGenerator(seed)

    def generate_heightmap(self, scale=0.05, octaves=4):
        heightmap = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                h = self.noise.perlin_noise(x, y, scale, octaves, 0.5)
                h = (h + 1.0) * 0.5
                row.append(min(1.0, max(0.0, h)))
            heightmap.append(row)
        return heightmap

    def generate_biome_map(self):
        heightmap = self.generate_heightmap(0.03, 6)
        biome_map = []
        for row in heightmap:
            biome_row = []
            for h in row:
                if h < 0.2:
                    biome_row.append("water")
                elif h < 0.35:
                    biome_row.append("sand")
                elif h < 0.6:
                    biome_row.append("grass")
                elif h < 0.8:
                    biome_row.append("forest")
                else:
                    biome_row.append("mountain")
            biome_map.append(biome_row)
        return biome_map


class DungeonGenerator:
    def __init__(self, width=40, height=40, seed=42):
        self.width = width
        self.height = height
        random.seed(seed)

    def generate(self, min_rooms=5, max_rooms=10):
        grid = [[1] * self.width for _ in range(self.height)]
        rooms = []

        for _ in range(random.randint(min_rooms, max_rooms)):
            rw = random.randint(3, 8)
            rh = random.randint(3, 8)
            rx = random.randint(1, self.width - rw - 1)
            ry = random.randint(1, self.height - rh - 1)

            if self._carve_room(grid, rx, ry, rw, rh):
                rooms.append((rx + rw // 2, ry + rh // 2, rw, rh))

        for i in range(len(rooms) - 1):
            x1, y1, _, _ = rooms[i]
            x2, y2, _, _ = rooms[i + 1]
            self._carve_corridor(grid, x1, y1, x2, y2)

        return grid, rooms

    def _carve_room(self, grid, x, y, w, h):
        for dy in range(-1, h + 1):
            for dx in range(-1, w + 1):
                if grid[y + dy][x + dx] == 0:
                    return False
        for dy in range(h):
            for dx in range(w):
                grid[y + dy][x + dx] = 0
        return True

    def _carve_corridor(self, grid, x1, y1, x2, y2):
        cx, cy = x1, y1
        while cx != x2:
            grid[cy][cx] = 0
            cx += 1 if cx < x2 else -1
        while cy != y2:
            grid[cy][cx] = 0
            cy += 1 if cy < y2 else -1
        grid[cy][cx] = 0


class QuestGenerator:
    def __init__(self, seed=42):
        random.seed(seed)
        self.objectives = ["kill", "collect", "escort", "deliver", "scout", "defend"]
        self.locations = ["ancient temple", "dark forest", "abandoned mine", "crystal cave",
                          "watchtower", "enemy camp", "hidden grove", "dragon peak"]
        self.enemies = ["goblins", "skeletons", "dark elves", "wolves", "bandits",
                        "elementals", "undead", "demons"]

    def generate(self, difficulty="medium"):
        objective = random.choice(self.objectives)
        location = random.choice(self.locations)
        enemy = random.choice(self.enemies)

        descriptions = {
            "kill": f"Eliminate the {enemy} threatening {location}",
            "collect": f"Retrieve the lost artifact from {location}",
            "escort": f"Escort the merchant safely through {location}",
            "deliver": f"Deliver supplies to the outpost at {location}",
            "scout": f"Scout {location} and report enemy movements",
            "defend": f"Defend {location} from {enemy} attack",
        }

        rewards = {"easy": (50, 100), "medium": (100, 250), "hard": (250, 500)}
        min_r, max_r = rewards.get(difficulty, (100, 250))

        return {
            "id": hashlib.md5(f"{objective}{location}{enemy}{random.random()}".encode()).hexdigest()[:8],
            "title": descriptions.get(objective, f"Quest at {location}"),
            "objective": objective,
            "location": location,
            "enemy": enemy,
            "difficulty": difficulty,
            "reward_gold": random.randint(min_r, max_r),
            "reward_xp": random.randint(min_r * 2, max_r * 3),
        }
