"""AI Story Engine — quests, dialogue, factions, lore, missions."""

from __future__ import annotations
import random
from typing import Optional, Any

from nicto_game.core.types import QuestDef, DialogNode, DialogResponse
from nicto_game.core.config import GameConfig, GameGenre


QUEST_PATTERNS: dict[str, list[dict[str, Any]]] = {
    "rpg": [
        {"name": "The Lost Artifact", "type": "fetch",
         "desc": "Retrieve the {artifact} from {location} and return it to {giver}."},
        {"name": "Cleanse the Nest", "type": "kill",
         "desc": "Eliminate {count} {enemies} terrorizing {location}."},
        {"name": "Escort Mission", "type": "escort",
         "desc": "Escort {target} safely through {location}."},
    ],
    "survival": [
        {"name": "Secure Shelter", "type": "build",
         "desc": "Build a shelter before nightfall in {location}."},
        {"name": "Hunt for Food", "type": "gather",
         "desc": "Hunt {count} {creatures} to restock supplies."},
        {"name": "Find a Cure", "type": "fetch",
         "desc": "Find {item} in the {location} to cure {target}."},
    ],
    "fps": [
        {"name": "Clear the Area", "type": "kill",
         "desc": "Eliminate {count} hostiles in {location}."},
        {"name": "Defend the Base", "type": "defend",
         "desc": "Defend {location} from an incoming assault."},
        {"name": "Intel Retrieval", "type": "fetch",
         "desc": "Retrieve classified intel from {location}."},
    ],
}

LOCATIONS = [
    "the Dark Forest", "the Forgotten Temple", "the Wasteland",
    "the Ancient Ruins", "the Frozen Pass", "the Crystal Caves",
    "the Sunken City", "the Dragon's Peak", "the Whispering Woods",
    "the Iron Mines", "the Lighthouse", "the Abandoned Fortress",
]

ARTIFACTS = [
    "Crystal of Eternity", "Amulet of Kings", "Orb of Scrying",
    "Blade of Dawn", "Shield of Faith", "Tome of Wisdom",
]

CREATURES = ["wolves", "bandits", "undead", "goblins", "mutants", "raiders"]


class StoryEngine:
    """Generates quests, dialogue, lore, factions, and narrative content."""

    def __init__(self):
        self.rng = random.Random()

    async def generate(self, config: GameConfig) -> dict[str, Any]:
        self.rng = random.Random(config.world.seed or random.randint(0, 2 ** 31))
        lore = self._generate_lore(config) if config.story.generate_lore else {}
        quests = self._generate_quests(config) if config.story.generate_quests else []
        dialogue = self._generate_main_story_dialogue(config) if config.story.generate_dialogue else []

        return {
            "lore": lore,
            "quests": quests,
            "dialogue": dialogue,
            "factions": [],
            "cinematics": [],
        }

    def _generate_lore(self, config: GameConfig) -> dict[str, str]:
        world_name = config.name.replace("_", " ")
        lore_pieces = {
            "history": f"The world of {world_name} was forged in an age of titans, "
                       f"when the {self.rng.choice(ARTIFACTS)} was hidden away to prevent its power from "
                       f"falling into the wrong hands.",
            "world": f"{world_name} is a land of diverse biomes, from {self.rng.choice(LOCATIONS)} "
                     f"to the {self.rng.choice(LOCATIONS)}. Ancient ruins dot the landscape, "
                     f"whispering secrets of a forgotten civilization.",
            "conflict": f"Tensions rise as {self.rng.choice(['The Guardians', 'The Free Folk', 'The Shadow Syndicate'])} "
                        f"seek to claim the {self.rng.choice(ARTIFACTS)} for their own purposes.",
        }
        return lore_pieces

    def _generate_quests(self, config: GameConfig) -> list[QuestDef]:
        patterns = QUEST_PATTERNS.get(config.genre.value, QUEST_PATTERNS.get("rpg", []))
        quests = []
        num = min(config.story.num_quests, len(patterns) * 2)

        for i in range(num):
            pattern = self.rng.choice(patterns)
            q = QuestDef(
                id=f"quest_{i}",
                name=pattern["name"],
                description=pattern["desc"].format(
                    artifact=self.rng.choice(ARTIFACTS),
                    location=self.rng.choice(LOCATIONS),
                    giver=self.rng.choice(["the Elder", "the Commander", "the Mystic"]),
                    count=self.rng.randint(3, 10),
                    enemies=self.rng.choice(CREATURES),
                    target=self.rng.choice(["the merchant caravan", "the lost patrol"]),
                    item=self.rng.choice(["a rare herb", "an ancient key", "a power cell"]),
                    creatures=self.rng.choice(CREATURES),
                ),
                objectives=self._generate_objectives(pattern["type"]),
                rewards={
                    "gold": self.rng.randint(50, 500),
                    "xp": self.rng.randint(100, 1000),
                },
                faction=self.rng.choice(["The Guardians", "The Free Folk", "The Shadow Syndicate"]),
                prerequisites=[] if i == 0 else [f"quest_{i - 1}"],
            )
            quests.append(q)
        return quests

    def _generate_objectives(self, quest_type: str) -> list[str]:
        objectives = {
            "fetch": ["Find the objective", "Retrieve it safely", "Return to the quest giver"],
            "kill": ["Locate the target area", "Eliminate all hostiles", "Report back"],
            "escort": ["Meet the escort target", "Guide them safely", "Ensure their survival"],
            "build": ["Gather materials", "Construct the structure", "Defend it if needed"],
            "gather": ["Find the gather zone", "Collect required resources", "Return safely"],
            "defend": ["Reach the defensive position", "Hold the line", "Eliminate the threat"],
        }
        return objectives.get(quest_type, ["Complete the objective"])

    def _generate_main_story_dialogue(self, config: GameConfig) -> list[DialogNode]:
        return [
            DialogNode(
                id="intro",
                text=f"Welcome to {config.name}. Your journey begins now. "
                     f"The fate of this world rests on your shoulders.",
                responses=[
                    DialogResponse(text="Tell me more about this world."),
                    DialogResponse(text="What is my first task?", quest_give="quest_0"),
                ],
            ),
            DialogNode(
                id="mid_game",
                text="You've proven yourself capable. But darker challenges await.",
                responses=[
                    DialogResponse(text="I'm ready."),
                    DialogResponse(text="I need to prepare first."),
                ],
            ),
        ]

    async def generate_cinematic_beat(self, quest: QuestDef, chapter: int = 1) -> str:
        beats = [
            f"CHAPTER {chapter}: {quest.name}",
            f"The hero ventures into {self.rng.choice(LOCATIONS)}...",
            f"Darkness gathers as {self.rng.choice(CREATURES)} approach...",
            f"Against all odds, victory is achieved.",
        ]
        return "\n".join(beats)
