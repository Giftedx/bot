"""OSRS Quest System"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from enum import Enum
import asyncio


class QuestDifficulty(Enum):
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    EXPERIENCED = "experienced"
    MASTER = "master"
    GRANDMASTER = "grandmaster"


class QuestStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class QuestRequirements:
    """Requirements to start a quest"""

    quest_points: int = 0
    quests: List[str] = None
    skills: Dict[str, int] = None
    items: List[str] = None
    combat_level: Optional[int] = None


@dataclass
class QuestRewards:
    """Rewards from completing a quest"""

    quest_points: int
    experience: Dict[str, int]  # skill -> xp
    items: Dict[str, int]  # item -> quantity
    unlocks: Set[str]


@dataclass
class QuestStep:
    """A single step in a quest"""

    description: str
    items_needed: List[str] = None
    skills_needed: Dict[str, int] = None
    combat_required: bool = False
    monster_to_kill: Optional[str] = None
    location: Optional[str] = None


class Quest:
    """Represents an OSRS quest"""

    def __init__(
        self,
        name: str,
        difficulty: QuestDifficulty,
        requirements: QuestRequirements,
        rewards: QuestRewards,
        steps: List[QuestStep],
    ):
        self.name = name
        self.difficulty = difficulty
        self.requirements = requirements
        self.rewards = rewards
        self.steps = steps


class QuestInstance:
    """An active quest instance for a player"""

    def __init__(self, quest: Quest, player_id: str):
        self.quest = quest
        self.player_id = player_id
        self.current_step = 0
        self.status = QuestStatus.IN_PROGRESS

    async def advance_step(self) -> str:
        """Advance to next quest step"""
        if self.status != QuestStatus.IN_PROGRESS:
            return "This quest is not in progress"

        if self.current_step >= len(self.quest.steps):
            self.status = QuestStatus.COMPLETED
            return f"Congratulations! You have completed {self.quest.name}!"

        current = self.quest.steps[self.current_step]
        self.current_step += 1

        return f"Step {self.current_step}: {current.description}"


class QuestManager:
    """Manages all quests and player progress"""

    def __init__(self):
        self.quests = self._load_quests()
        self.active_quests: Dict[str, QuestInstance] = {}

    def _load_quests(self) -> Dict[str, Quest]:
        """Load all quest definitions"""
        return {
            "Cook's Assistant": Quest(
                name="Cook's Assistant",
                difficulty=QuestDifficulty.NOVICE,
                requirements=QuestRequirements(),
                rewards=QuestRewards(
                    quest_points=1, experience={"cooking": 300}, items={}, unlocks={"Cooking Guild"}
                ),
                steps=[
                    QuestStep(
                        description="Talk to the Cook in Lumbridge Castle's kitchen.",
                        location="Lumbridge Castle",
                    ),
                    QuestStep(
                        description="Gather ingredients: Bucket of milk, Pot of flour, Egg",
                        items_needed=["Bucket of milk", "Pot of flour", "Egg"],
                    ),
                    QuestStep(description="Return the ingredients to the Cook."),
                ],
            ),
            "Dragon Slayer": Quest(
                name="Dragon Slayer",
                difficulty=QuestDifficulty.EXPERIENCED,
                requirements=QuestRequirements(
                    quest_points=32,
                    skills={"crafting": 8, "smithing": 34, "mining": 35},
                    combat_level=40,
                ),
                rewards=QuestRewards(
                    quest_points=2,
                    experience={"strength": 18650, "defence": 18650},
                    items={"Anti-dragon shield": 1},
                    unlocks={"Ability to wear rune platebody", "Access to Crandor"},
                ),
                steps=[
                    QuestStep(
                        description="Talk to the Guildmaster in the Champions' Guild.",
                        location="Champions' Guild",
                    ),
                    QuestStep(
                        description="Get the map pieces from Melzar, Oracle, and Wormbrain.",
                        items_needed=["Melzar's map", "Oracle's map", "Wormbrain's map"],
                    ),
                    QuestStep(
                        description="Buy or make a boat to sail to Crandor.",
                        skills_needed={"crafting": 8},
                    ),
                    QuestStep(
                        description="Defeat Elvarg.",
                        combat_required=True,
                        monster_to_kill="Elvarg",
                        items_needed=["Anti-dragon shield"],
                    ),
                ],
            ),
            # Add more quests...
        }

    async def start_quest(self, player_id: str, quest_name: str) -> Optional[QuestInstance]:
        """Start a new quest for a player"""
        quest = self.quests.get(quest_name)
        if not quest:
            return None

        # Check if already in progress
        if f"{player_id}:{quest_name}" in self.active_quests:
            return None

        # Create new instance
        instance = QuestInstance(quest, player_id)
        self.active_quests[f"{player_id}:{quest_name}"] = instance

        return instance

    async def get_quest_progress(self, player_id: str, quest_name: str) -> Optional[QuestInstance]:
        """Get a player's progress in a quest"""
        return self.active_quests.get(f"{player_id}:{quest_name}")

    def get_available_quests(
        self,
        player_id: str,
        completed_quests: Set[str],
        quest_points: int,
        skills: Dict[str, int],
        combat_level: int,
    ) -> List[str]:
        """Get list of quests available to start"""
        available = []

        for name, quest in self.quests.items():
            # Skip completed quests
            if name in completed_quests:
                continue

            # Check requirements
            reqs = quest.requirements

            if reqs.quest_points > quest_points:
                continue

            if reqs.quests and not all(q in completed_quests for q in reqs.quests):
                continue

            if reqs.skills and not all(
                skills.get(skill, 0) >= level for skill, level in reqs.skills.items()
            ):
                continue

            if reqs.combat_level and combat_level < reqs.combat_level:
                continue

            available.append(name)

        return available

    async def complete_quest(self, player_id: str, quest_name: str) -> Optional[QuestRewards]:
        """Complete a quest and get rewards"""
        instance = self.active_quests.get(f"{player_id}:{quest_name}")
        if not instance or instance.status != QuestStatus.IN_PROGRESS:
            return None

        instance.status = QuestStatus.COMPLETED
        return instance.quest.rewards
