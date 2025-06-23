"""OSRS Skill System"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from enum import Enum
import math
import random
import asyncio


class SkillType(Enum):
    ATTACK = "attack"
    STRENGTH = "strength"
    DEFENCE = "defence"
    RANGED = "ranged"
    PRAYER = "prayer"
    MAGIC = "magic"
    RUNECRAFT = "runecraft"
    HITPOINTS = "hitpoints"
    CRAFTING = "crafting"
    MINING = "mining"
    SMITHING = "smithing"
    FISHING = "fishing"
    COOKING = "cooking"
    FIREMAKING = "firemaking"
    WOODCUTTING = "woodcutting"
    AGILITY = "agility"
    HERBLORE = "herblore"
    THIEVING = "thieving"
    FLETCHING = "fletching"
    SLAYER = "slayer"
    FARMING = "farming"
    CONSTRUCTION = "construction"
    HUNTER = "hunter"


@dataclass
class SkillRequirement:
    """Requirements for a skill action"""

    level: int
    items: Dict[str, int] = None  # item -> quantity
    quests: List[str] = None


@dataclass
class SkillReward:
    """Rewards for completing a skill action"""

    experience: float
    items: Dict[str, int] = None  # item -> quantity
    pet_chance: float = 0.0


class SkillAction:
    """Represents a skill training action"""

    def __init__(
        self,
        name: str,
        skill: SkillType,
        requirements: SkillRequirement,
        rewards: SkillReward,
        ticks_per_action: int,
    ):
        self.name = name
        self.skill = skill
        self.requirements = requirements
        self.rewards = rewards
        self.ticks_per_action = ticks_per_action


class SkillManager:
    """Manages player skills and experience"""

    def __init__(self):
        self.actions = self._load_skill_actions()
        self.player_skills: Dict[str, Dict[SkillType, float]] = {}  # player_id -> skill -> xp

    def _load_skill_actions(self) -> Dict[str, SkillAction]:
        """Load all skill training actions"""
        return {
            "Oak logs": SkillAction(
                name="Oak logs",
                skill=SkillType.WOODCUTTING,
                requirements=SkillRequirement(level=15, items={"Bronze axe": 1}),
                rewards=SkillReward(experience=37.5, items={"Oak logs": 1}, pet_chance=0.0008),
                ticks_per_action=4,
            ),
            "Copper ore": SkillAction(
                name="Copper ore",
                skill=SkillType.MINING,
                requirements=SkillRequirement(level=1, items={"Bronze pickaxe": 1}),
                rewards=SkillReward(experience=17.5, items={"Copper ore": 1}, pet_chance=0.0004),
                ticks_per_action=3,
            ),
            "Air rune": SkillAction(
                name="Air rune",
                skill=SkillType.RUNECRAFT,
                requirements=SkillRequirement(level=1, items={"Pure essence": 1}),
                rewards=SkillReward(experience=5.0, items={"Air rune": 1}),
                ticks_per_action=2,
            ),
            # Add more actions...
        }

    def get_level(self, experience: float) -> int:
        """Convert experience to level"""
        points = 0
        level = 1

        while level < 99:
            points += math.floor(level + 300 * (2 ** (level / 7.0)))
            if experience < points / 4:
                return level
            level += 1

        return 99

    def get_experience(self, level: int) -> float:
        """Get experience required for level"""
        points = 0
        for i in range(1, level):
            points += math.floor(i + 300 * (2 ** (i / 7.0)))
        return points / 4

    def get_player_skills(self, player_id: str) -> Dict[SkillType, float]:
        """Get all skills and their experience for a player"""
        if player_id not in self.player_skills:
            self.player_skills[player_id] = {skill: 0.0 for skill in SkillType}
            # Set initial hitpoints
            self.player_skills[player_id][SkillType.HITPOINTS] = self.get_experience(10)

        return self.player_skills[player_id]

    def get_skill_level(self, player_id: str, skill: SkillType) -> int:
        """Get current level in a skill"""
        skills = self.get_player_skills(player_id)
        return self.get_level(skills[skill])

    def get_total_level(self, player_id: str) -> int:
        """Get total level across all skills"""
        skills = self.get_player_skills(player_id)
        return sum(self.get_level(xp) for xp in skills.values())

    async def perform_action(
        self,
        player_id: str,
        action_name: str,
        inventory: Dict[str, int],
        completed_quests: Set[str],
    ) -> Optional[SkillReward]:
        """Attempt to perform a skill action"""
        action = self.actions.get(action_name)
        if not action:
            return None

        # Check level requirement
        if self.get_skill_level(player_id, action.skill) < action.requirements.level:
            return None

        # Check item requirements
        if action.requirements.items:
            for item, quantity in action.requirements.items.items():
                if inventory.get(item, 0) < quantity:
                    return None

        # Check quest requirements
        if action.requirements.quests and not all(
            q in completed_quests for q in action.requirements.quests
        ):
            return None

        # Wait for action to complete
        await asyncio.sleep(action.ticks_per_action * 0.6)  # 0.6s per game tick

        # Add experience
        skills = self.get_player_skills(player_id)
        skills[action.skill] += action.rewards.experience

        # Roll for pet
        if action.rewards.pet_chance > 0 and random.random() < action.rewards.pet_chance:
            if action.rewards.items is None:
                action.rewards.items = {}
            action.rewards.items[f"{action.skill.value.title()} pet"] = 1

        return action.rewards

    def get_virtual_level(self, experience: float) -> int:
        """Get virtual level (above 99) based on experience"""
        if experience < self.get_experience(99):
            return self.get_level(experience)

        level = 99
        points = 0

        while True:
            points += math.floor(level + 300 * (2 ** (level / 7.0)))
            if experience < points / 4:
                return level
            level += 1
