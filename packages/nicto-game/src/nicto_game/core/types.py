"""Shared types and data structures for the NICTO Omega Game Engine."""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum, Enum
from typing import Optional, Any


class TileType(IntEnum):
    EMPTY = 0
    WALL = 1
    WATER = 2
    TREE = 3
    DOOR = 4
    ENEMY_SPAWN = 5
    ITEM = 6
    EXIT = 7
    NPC_SPAWN = 8
    BRIDGE = 9
    BUILDING = 10
    ROAD = 11
    SAND = 12
    SNOW = 13
    LAVA = 14
    BUSH = 15
    ROCK = 16
    CHEST = 17
    TRAP = 18
    SIGN = 19
    CAMPFIRE = 20


TILE_COLORS: dict[TileType, tuple[int, int, int]] = {
    TileType.EMPTY: (40, 40, 40),
    TileType.WALL: (100, 100, 100),
    TileType.WATER: (20, 60, 120),
    TileType.TREE: (20, 80, 30),
    TileType.DOOR: (120, 80, 40),
    TileType.ENEMY_SPAWN: (200, 30, 30),
    TileType.ITEM: (200, 200, 30),
    TileType.EXIT: (30, 200, 30),
    TileType.NPC_SPAWN: (30, 30, 200),
    TileType.BRIDGE: (100, 70, 40),
    TileType.BUILDING: (150, 100, 70),
    TileType.ROAD: (80, 70, 60),
    TileType.SAND: (180, 170, 100),
    TileType.SNOW: (200, 210, 220),
    TileType.LAVA: (200, 50, 10),
    TileType.BUSH: (30, 100, 20),
    TileType.ROCK: (90, 85, 80),
    TileType.CHEST: (160, 120, 30),
    TileType.TRAP: (100, 10, 10),
    TileType.SIGN: (140, 120, 60),
    TileType.CAMPFIRE: (200, 100, 20),
}

TILE_WALKABLE = {
    TileType.EMPTY, TileType.DOOR, TileType.ROAD,
    TileType.BRIDGE, TileType.SAND, TileType.EXIT,
    TileType.ITEM, TileType.SIGN, TileType.CAMPFIRE,
    TileType.CHEST,
}


@dataclass
class GameMap:
    width: int
    height: int
    tiles: list[list[int]]
    heightmap: list[list[float]] = field(default_factory=list)
    regions: dict[str, list[tuple[int, int]]] = field(default_factory=dict)
    spawn_points: dict[str, tuple[int, int]] = field(default_factory=dict)
    properties: dict[str, Any] = field(default_factory=dict)

    def get_tile(self, x: int, y: int) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return TileType.WALL

    def is_walkable(self, x: int, y: int) -> bool:
        return TileType(self.get_tile(x, y)) in TILE_WALKABLE

    def find_empty_tile(self, rng=None) -> Optional[tuple[int, int]]:
        import random
        rg = rng or random
        empties = [(x, y) for y in range(self.height) for x in range(self.width)
                    if TileType(self.tiles[y][x]) in TILE_WALKABLE]
        return rg.choice(empties) if empties else None


class Biome(Enum):
    PLAINS = "plains"
    FOREST = "forest"
    DESERT = "desert"
    TUNDRA = "tundra"
    MOUNTAINS = "mountains"
    SWAMP = "swamp"
    OCEAN = "ocean"
    SAVANNA = "savanna"
    JUNGLE = "jungle"
    SNOW = "snow"
    VOLCANIC = "volcanic"
    CAVE = "cave"


@dataclass
class CharacterDef:
    name: str
    role: str
    health: float = 100.0
    speed: float = 3.0
    damage: float = 10.0
    faction: str = "neutral"
    dialog_tree: list[DialogNode] = field(default_factory=list)
    behavior: str = "passive"
    inventory: list[str] = field(default_factory=list)


@dataclass
class ItemDef:
    name: str
    item_type: str
    value: float = 0.0
    effect: str = ""
    description: str = ""
    stackable: bool = True


@dataclass
class QuestDef:
    id: str
    name: str
    description: str
    objectives: list[str] = field(default_factory=list)
    rewards: dict[str, float] = field(default_factory=dict)
    faction: str = "neutral"
    prerequisites: list[str] = field(default_factory=list)


@dataclass
class DialogNode:
    id: str
    text: str
    responses: list[DialogResponse] = field(default_factory=list)
    conditions: dict[str, Any] = field(default_factory=dict)


@dataclass
class DialogResponse:
    text: str
    next_node: Optional[str] = None
    quest_give: Optional[str] = None
    requires_item: Optional[str] = None
