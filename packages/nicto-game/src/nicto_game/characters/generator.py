"""AI Character Generator — NPCs, factions, behaviors, animations."""

from __future__ import annotations
import random
from typing import Optional, Any

from nicto_game.core.types import CharacterDef, DialogNode, DialogResponse
from nicto_game.core.config import GameConfig, GameGenre


ROLE_TEMPLATES: dict[str, list[str]] = {
    "fps": ["soldier", "guard", "commander", "scientist", "civilian"],
    "rpg": ["merchant", "blacksmith", "innkeeper", "guard", "king",
            "wizard", "thief", "healer", "quest_giver", "villager"],
    "dungeon": ["prisoner", "guard", "wizard", "treasure_keeper", "ghost"],
    "survival": ["survivor", "trader", "hunter", "scavenger", "doctor"],
    "adventure": ["explorer", "guide", "ancient_guardian", "sage", "merchant"],
}


class CharacterGenerator:
    """Generates characters, NPCs, factions, and dialogue."""

    def __init__(self):
        self.rng = random.Random()

    async def generate(self, config: GameConfig, num_npcs: int = 0) -> list[CharacterDef]:
        self.rng = random.Random(config.world.seed or random.randint(0, 2 ** 31))
        n = num_npcs or config.world.npcs
        if n == 0:
            return []

        roles = ROLE_TEMPLATES.get(config.genre.value, ["villager", "guard", "merchant"])
        characters = []
        for i in range(n):
            role = self.rng.choice(roles)
            char = self._create_character(i, role, config)
            characters.append(char)
        return characters

    def _create_character(self, idx: int, role: str, config: GameConfig) -> CharacterDef:
        name = self._generate_name()
        faction = self._assign_faction(role, config)
        behavior = self._get_behavior(role)

        char = CharacterDef(
            name=name,
            role=role,
            health=self._roll_stat(80, 150, role),
            speed=self._roll_stat(2, 4.5, role),
            damage=self._roll_stat(0, 25, role),
            faction=faction,
            behavior=behavior,
            dialog_tree=self._generate_dialog(name, role, faction, config),
            inventory=self._generate_inventory(role),
        )
        return char

    def _generate_name(self) -> str:
        prefixes = ["Ald", "Bran", "Cor", "Dal", "El", "Far", "Gar", "Hav",
                     "Ith", "Jor", "Kal", "Lor", "Mar", "Nor", "Or", "Pal"]
        suffixes = ["ic", "an", "on", "ar", "en", "or", "is", "us", "os", "a"]
        return self.rng.choice(prefixes) + self.rng.choice(suffixes)

    def _assign_faction(self, role: str, config: GameConfig) -> str:
        factions = {
            "quest_giver": "peaceful", "merchant": "neutral",
            "guard": "lawful", "king": "lawful",
            "soldier": "lawful", "prisoner": "outlaw",
            "thief": "outlaw", "hunter": "neutral",
        }
        return factions.get(role, "neutral")

    def _get_behavior(self, role: str) -> str:
        behavior_map = {
            "guard": "hostile", "soldier": "hostile", "prisoner": "flee",
            "merchant": "passive", "innkeeper": "passive", "villager": "passive",
            "healer": "friendly", "quest_giver": "friendly",
            "hunter": "neutral", "trader": "passive",
        }
        return behavior_map.get(role, "passive")

    def _roll_stat(self, low: float, high: float, role: str) -> float:
        boost = 0
        if role in ("boss", "king", "ancient_guardian"):
            boost = 30
        return round(self.rng.uniform(low, high) + boost, 1)

    def _generate_dialog(self, name: str, role: str, faction: str,
                         config: GameConfig) -> list[DialogNode]:
        greetings = {
            "merchant": f"Welcome to my shop, traveler. Would you like to see my wares?",
            "guard": f"Halt! State your business in {config.name}.",
            "innkeeper": f"Need a room for the night? We have the best beds in town.",
            "healer": f"You look injured. Let me help you.",
            "quest_giver": f"I have a task that needs doing. Are you interested?",
            "villager": f"Good day to you. Have you heard the news from the capital?",
        }
        greeting = greetings.get(role, f"Hello there.")

        farewells = {
            "merchant": "Come back anytime!",
            "guard": "Stay out of trouble.",
            "innkeeper": "Rest well.",
        }
        farewell = farewells.get(role, "Farewell.")

        return [
            DialogNode(id="greeting", text=greeting, responses=[
                DialogResponse(text="Tell me more about yourself."),
                DialogResponse(text="Goodbye.", next_node="farewell"),
            ]),
            DialogNode(id="farewell", text=farewell),
        ]

    def _generate_inventory(self, role: str) -> list[str]:
        loot: dict[str, list[str]] = {
            "merchant": ["gold", "potion", "scroll", "map"],
            "guard": ["sword", "shield", "ration"],
            "healer": ["health_potion", "antidote", "bandage"],
            "hunter": ["bow", "arrow", "meat", "pelt"],
            "prisoner": ["rusty_key", "bone", "rag"],
            "soldier": ["rifle", "ammo", "grenade"],
            "villager": ["bread", "water"],
            "innkeeper": ["key", "food"],
            "blacksmith": ["hammer", "ingot"],
            "wizard": ["scroll", "potion", "crystal"],
            "thief": ["lockpick", "gold", "dagger"],
            "king": ["crown", "gold", "scepter"],
            "trader": ["goods", "coin", "map"],
            "survivor": ["water", "food", "bandage"],
            "scavenger": ["scrap", "battery", "medkit"],
            "doctor": ["medicine", "bandage", "scalpel"],
            "explorer": ["compass", "map", "rope"],
            "guide": ["torch", "map", "food"],
            "ancient_guardian": ["key", "crystal", "scroll"],
            "sage": ["book", "scroll", "potion"],
        }
        inv = loot.get(role, ["coin", "ration", "canteen"])
        self.rng.shuffle(inv)
        return inv[:self.rng.randint(1, max(1, len(inv)))]

    def generate_factions(self, config: GameConfig) -> dict[str, dict[str, Any]]:
        faction_templates: list[dict[str, Any]] = [
            {"name": "The Guardians", "alignment": "lawful",
             "values": ["protection", "order", "justice"],
             "color": "blue", "symbol": "shield"},
            {"name": "The Free Folk", "alignment": "neutral",
             "values": ["freedom", "trade", "exploration"],
             "color": "green", "symbol": "compass"},
            {"name": "The Shadow Syndicate", "alignment": "chaotic",
             "values": ["power", "wealth", "secrets"],
             "color": "red", "symbol": "dagger"},
        ]
        factions = {}
        for ft in faction_templates[:config.story.num_factions]:
            factions[ft["name"]] = ft
        return factions
