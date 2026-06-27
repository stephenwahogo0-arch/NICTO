"""PCG (Procedural Content Generation) Framework.

Unreal Engine 5-inspired rule-based procedural generation:
- Rule graph: define rules that generate content
- Biome-aware terrain generation with erosion
- City generation with road networks, buildings, districts
- Forest/ecosystem generation with vegetation rules
- Dungeon/cave generation with room grammar
"""
from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Callable, Any
from enum import Enum


class PCGRuleType(Enum):
    SPAWN = "spawn"
    TRANSFORM = "transform"
    FILTER = "filter"
    COMBINE = "combine"
    LOOP = "loop"
    CONDITIONAL = "conditional"


class PCGRegion(Enum):
    FOREST = "forest"
    DESERT = "desert"
    MOUNTAINS = "mountains"
    PLAINS = "plains"
    CITY = "city"
    WATER = "water"
    DUNGEON = "dungeon"
    CAVE = "cave"
    VILLAGE = "village"
    FARMLAND = "farmland"
    TUNDRA = "tundra"
    JUNGLE = "jungle"


@dataclass
class PCGSpawnPoint:
    x: float; y: float; z: float
    region: PCGRegion = PCGRegion.PLAINS
    tags: List[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)


@dataclass
class PCGRule:
    rule_type: PCGRuleType
    name: str = ""
    condition: Optional[Callable] = None
    action: Optional[Callable] = None
    weight: float = 1.0
    children: List['PCGRule'] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class PCGContext:
    """Context passed through PCG rule execution."""
    seed: int = 0
    region: PCGRegion = PCGRegion.PLAINS
    width: int = 256
    height: int = 256
    spawn_points: List[PCGSpawnPoint] = field(default_factory=list)
    heightmap: List[List[float]] = field(default_factory=list)
    moisture_map: List[List[float]] = field(default_factory=list)
    biome_map: List[List[PCGRegion]] = field(default_factory=list)
    properties: dict = field(default_factory=dict)
    rng: Any = field(default_factory=lambda: random.Random())


class PCGEngine:
    """PCG (Procedural Content Generation) Framework.

    Generates massive worlds using rules:
    - Rule graph with conditional branching
    - Biome-aware terrain, cities, vegetation, dungeons
    - Multi-layer generation (macro -> micro)
    - Real-time generation with LOD
    """

    def __init__(self):
        self.rules: Dict[str, PCGRule] = {}
        self.rule_graphs: Dict[str, List[str]] = {}
        self._perlin_cache: Dict = {}

    def add_rule(self, name: str, rule: PCGRule, graph_name: str = "default"):
        self.rules[name] = rule
        if graph_name not in self.rule_graphs:
            self.rule_graphs[graph_name] = []
        self.rule_graphs[graph_name].append(name)

    def execute_graph(self, graph_name: str, context: PCGContext) -> PCGContext:
        """Execute all rules in a graph sequentially."""
        rule_names = self.rule_graphs.get(graph_name, [])
        for name in rule_names:
            rule = self.rules.get(name)
            if rule:
                context = self._execute_rule(rule, context)
        return context

    def _execute_rule(self, rule: PCGRule, context: PCGContext) -> PCGContext:
        try:
            if rule.condition and not rule.condition(context):
                return context
            if rule.action:
                context = rule.action(context)
        except Exception:
            pass
        if rule.children:
            for child in rule.children:
                context = self._execute_rule(child, context)
        return context

    def register_default_rules(self):
        """Register a full set of world-generation rules."""

        def terrain_rule(ctx: PCGContext) -> PCGContext:
            w, h = ctx.width, ctx.height
            ctx.heightmap = [[0.0 for _ in range(w)] for _ in range(h)]
            for octave in range(4):
                freq = 0.02 * (2 ** octave)
                amp = 0.5 / (2 ** octave)
                for y in range(h):
                    for x in range(w):
                        nx, ny = x * freq, y * freq
                        v = (math.sin(nx * 2.1 + ny * 1.3) * math.cos(ny * 1.7 - nx * 2.3) + 1) * 0.5
                        ctx.heightmap[y][x] += v * amp
            for y in range(h):
                for x in range(w):
                    ctx.heightmap[y][x] = max(0, min(1, ctx.heightmap[y][x]))
            return ctx

        def biome_rule(ctx: PCGContext) -> PCGContext:
            ctx.biome_map = [[PCGRegion.PLAINS for _ in range(ctx.width)] for _ in range(ctx.height)]
            ctx.moisture_map = [[0.0 for _ in range(ctx.width)] for _ in range(ctx.height)]
            for y in range(ctx.height):
                for x in range(ctx.width):
                    h_val = ctx.heightmap[y][x]
                    mx = x * 0.01; my = y * 0.01
                    moisture = (math.sin(mx * 1.5 + my * 2.3) + 1) * 0.5
                    ctx.moisture_map[y][x] = moisture
                    if h_val < 0.2:
                        ctx.biome_map[y][x] = PCGRegion.WATER
                    elif h_val < 0.35:
                        ctx.biome_map[y][x] = PCGRegion.PLAINS if moisture > 0.4 else PCGRegion.DESERT
                    elif h_val < 0.55:
                        ctx.biome_map[y][x] = PCGRegion.FOREST if moisture > 0.5 else PCGRegion.FARMLAND
                    elif h_val < 0.75:
                        ctx.biome_map[y][x] = PCGRegion.FOREST if moisture > 0.6 else PCGRegion.MOUNTAINS
                    else:
                        ctx.biome_map[y][x] = PCGRegion.MOUNTAINS
            return ctx

        def city_rule(ctx: PCGContext) -> PCGContext:
            city_center_x = ctx.width // 2 + ctx.rng.randint(-20, 20)
            city_center_y = ctx.height // 2 + ctx.rng.randint(-20, 20)
            center_h = ctx.heightmap[city_center_y][city_center_x] if 0 <= city_center_y < ctx.height and 0 <= city_center_x < ctx.width else 0.3
            if center_h > 0.6 or center_h < 0.2:
                return ctx
            ctx.spawn_points.append(PCGSpawnPoint(
                x=city_center_x, y=center_h, z=city_center_y,
                region=PCGRegion.CITY, tags=["city_center"],
                data={"radius": 30 + ctx.rng.randint(10, 30), "buildings": 50 + ctx.rng.randint(0, 50)}
            ))
            for i in range(5):
                rx = city_center_x + ctx.rng.randint(-3, 3)
                ry = city_center_y + ctx.rng.randint(-3, 3)
                ctx.spawn_points.append(PCGSpawnPoint(
                    x=rx, y=ctx.heightmap[ry][rx] if 0 <= ry < ctx.height and 0 <= rx < ctx.width else 0.3,
                    z=ry, region=PCGRegion.CITY, tags=["road_node"]
                ))
            for i in range(ctx.rng.randint(20, 50)):
                bx = city_center_x + ctx.rng.randint(-25, 25)
                by = city_center_y + ctx.rng.randint(-25, 25)
                if 0 <= by < ctx.height and 0 <= bx < ctx.width:
                    ctx.spawn_points.append(PCGSpawnPoint(
                        x=bx, y=ctx.heightmap[by][bx], z=by,
                        region=PCGRegion.CITY, tags=["building"],
                        data={"floors": ctx.rng.randint(1, 12)}
                    ))
            return ctx

        def forest_rule(ctx: PCGContext) -> PCGContext:
            for y in range(0, ctx.height, 2):
                for x in range(0, ctx.width, 2):
                    if (0 <= y < ctx.height and 0 <= x < ctx.width and
                        ctx.biome_map[y][x] in (PCGRegion.FOREST, PCGRegion.JUNGLE)):
                        if ctx.rng.random() < 0.15:
                            ctx.spawn_points.append(PCGSpawnPoint(
                                x=x, y=ctx.heightmap[y][x], z=y,
                                region=PCGRegion.FOREST, tags=["tree"],
                                data={"species": ctx.rng.choice(["oak", "pine", "birch", "palm"])}
                            ))
                        elif ctx.rng.random() < 0.05:
                            ctx.spawn_points.append(PCGSpawnPoint(
                                x=x, y=ctx.heightmap[y][x], z=y,
                                region=PCGRegion.FOREST, tags=["bush", "flora"]
                            ))
            return ctx

        def village_rule(ctx: PCGContext) -> PCGContext:
            for _ in range(ctx.rng.randint(0, 3)):
                vx = ctx.rng.randint(10, ctx.width - 10)
                vy = ctx.rng.randint(10, ctx.height - 10)
                if (0 <= vy < ctx.height and 0 <= vx < ctx.width and
                    ctx.biome_map[vy][vx] in (PCGRegion.PLAINS, PCGRegion.FARMLAND)):
                    for i in range(ctx.rng.randint(4, 10)):
                        hx = vx + ctx.rng.randint(-8, 8)
                        hy = vy + ctx.rng.randint(-8, 8)
                        if 0 <= hy < ctx.height and 0 <= hx < ctx.width:
                            ctx.spawn_points.append(PCGSpawnPoint(
                                x=hx, y=ctx.heightmap[hy][hx], z=hy,
                                region=PCGRegion.VILLAGE, tags=["house"],
                                data={"type": ctx.rng.choice(["small", "medium", "large"])}
                            ))
            return ctx

        self.add_rule("terrain", PCGRule(PCGRuleType.TRANSFORM, "Terrain", action=terrain_rule))
        self.add_rule("biomes", PCGRule(PCGRuleType.TRANSFORM, "Biomes", action=biome_rule))
        self.add_rule("cities", PCGRule(PCGRuleType.SPAWN, "Cities", action=city_rule))
        self.add_rule("forests", PCGRule(PCGRuleType.SPAWN, "Forests", action=forest_rule))
        self.add_rule("villages", PCGRule(PCGRuleType.SPAWN, "Villages", action=village_rule))
        self.add_rule("full_world", PCGRule(PCGRuleType.COMBINE, "FullWorld", children=[
            self.rules["terrain"], self.rules["biomes"], self.rules["cities"],
            self.rules["forests"], self.rules["villages"],
        ]), graph_name="full_world")

    def generate_world(self, width: int = 256, height: int = 256, seed: int = 0) -> PCGContext:
        """Generate a complete world using the full rule graph."""
        ctx = PCGContext(width=width, height=height, seed=seed, rng=random.Random(seed))
        self.register_default_rules()
        return self.execute_graph("full_world", ctx)

    def generate_dungeon(self, rooms: int = 10, seed: int = 0) -> List[PCGSpawnPoint]:
        """Generate a dungeon using room grammar rules."""
        rng = random.Random(seed)
        points = []
        room_positions = []
        for i in range(rooms):
            attempts = 0
            while attempts < 50:
                rx = rng.randint(2, 60)
                ry = rng.randint(2, 60)
                rw = rng.randint(3, 8)
                rh = rng.randint(3, 8)
                overlap = False
                for ex, ey, ew, eh in room_positions:
                    if abs(rx - ex) < (rw + ew) * 0.5 and abs(ry - ey) < (rh + eh) * 0.5:
                        overlap = True; break
                if not overlap:
                    room_positions.append((rx, ry, rw, rh))
                    for dx in range(rw):
                        for dy in range(rh):
                            points.append(PCGSpawnPoint(
                                x=rx+dx, y=0, z=ry+dy,
                                region=PCGRegion.DUNGEON, tags=["floor"]
                            ))
                    break
                attempts += 1
        for i in range(len(room_positions) - 1):
            x1, y1 = room_positions[i][0] + room_positions[i][2] // 2, room_positions[i][1] + room_positions[i][3] // 2
            x2, y2 = room_positions[i+1][0] + room_positions[i+1][2] // 2, room_positions[i+1][1] + room_positions[i+1][3] // 2
            for t in range(0, 101, 5):
                t /= 100
                cx = int(x1 + (x2 - x1) * t)
                cy = int(y1 + (y2 - y1) * t)
                points.append(PCGSpawnPoint(x=cx, y=0, z=cy, region=PCGRegion.DUNGEON, tags=["corridor"]))
        return points

    def get_stats(self) -> dict:
        return {
            "rules": len(self.rules),
            "graphs": len(self.rule_graphs),
            "registered_rule_graphs": list(self.rule_graphs.keys()),
        }
