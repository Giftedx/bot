"""OSRS game models and data structures"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class SkillType(Enum):
    """OSRS skill types"""

    ATTACK = "attack"
    STRENGTH = "strength"
    DEFENCE = "defence"
    HITPOINTS = "hitpoints"
    RANGED = "ranged"
    PRAYER = "prayer"
    MAGIC = "magic"
    MINING = "mining"
    SMITHING = "smithing"
    FISHING = "fishing"
    COOKING = "cooking"
    WOODCUTTING = "woodcutting"
    FIREMAKING = "firemaking"
    CRAFTING = "crafting"
    FLETCHING = "fletching"
    AGILITY = "agility"
    HERBLORE = "herblore"
    THIEVING = "thieving"
    SLAYER = "slayer"
    FARMING = "farming"
    RUNECRAFT = "runecraft"
    CONSTRUCTION = "construction"
    HUNTER = "hunter"


@dataclass
class Skill:
    """Represents a trainable skill"""

    type: SkillType
    level: int = 1
    xp: int = 0

    def add_xp(self, amount: int) -> bool:
        """Add XP to the skill and return True if leveled up"""
        self.xp += amount
        old_level = self.level
        self.level = self._xp_to_level(self.xp)
        return self.level > old_level


@dataclass
class Equipment:
    """Represents equipped items"""

    weapon: Optional[dict] = None
    shield: Optional[dict] = None
    helmet: Optional[dict] = None
    body: Optional[dict] = None
    legs: Optional[dict] = None
    boots: Optional[dict] = None
    gloves: Optional[dict] = None
    amulet: Optional[dict] = None
    ring: Optional[dict] = None
    cape: Optional[dict] = None
    ammo: Optional[dict] = None

    def get_bonus(self, bonus_type: str) -> int:
        """Get total equipment bonus of specified type"""
        total = 0
        for slot in self.__dict__.values():
            if slot:
                total += slot.get("bonuses", {}).get(bonus_type, 0)
        return total


@dataclass
class InventoryItem:
    """Represents an item in an inventory"""

    id: int
    name: str
    quantity: int = 1
    stackable: bool = False
    noted: bool = False
    equipped: bool = False


@dataclass
class Item:
    """Represents an in-game item"""

    id: int
    name: str
    description: str
    tradeable: bool = True
    stackable: bool = False
    equipable: bool = False
    slot: Optional[str] = None
    bonuses: Dict[str, int] = field(default_factory=dict)
    requirements: Dict[str, int] = field(default_factory=dict)
    value: int = 0


@dataclass
class Player:
    """Represents a player character"""

    id: int
    name: str
    skills: Dict[SkillType, Skill] = field(default_factory=dict)
    inventory: List[InventoryItem] = field(default_factory=list)
    equipment: Equipment = field(default_factory=Equipment)
    prayer_points: int = 0
    run_energy: int = 100
    combat_stats: Dict[str, float] = field(default_factory=dict)
    gold: int = 0

    def __post_init__(self) -> None:
        """Initialize default skills and stats"""
        if not self.skills:
            self.skills = {
                skill_type: Skill(type=skill_type) for skill_type in SkillType
            }
            # Set Hitpoints to 10
            self.skills[SkillType.HITPOINTS].level = 10
            self.skills[SkillType.HITPOINTS].xp = self.xp_for_level(10)

        if not self.combat_stats:
            self.combat_stats = {
                "attack_bonus": 0,
                "strength_bonus": 0,
                "defence_bonus": 0,
                "magic_bonus": 0,
                "ranged_bonus": 0,
                "prayer_bonus": 0,
            }

    @staticmethod
    def xp_for_level(level: int) -> int:
        """Calculate XP required for a given level using OSRS formula"""
        total = 0
        for i in range(1, level):
            total += int(i + 300 * (2 ** (i / 7.0)))
        return int(total / 4)

    def get_combat_level(self) -> int:
        """Calculate combat level using OSRS formula"""
        base = 0.25 * (
            self.skills[SkillType.DEFENCE].level
            + self.skills[SkillType.HITPOINTS].level
            + (self.skills[SkillType.PRAYER].level // 2)
        )

        melee = 0.325 * (
            self.skills[SkillType.ATTACK].level + self.skills[SkillType.STRENGTH].level
        )

        ranged = 0.325 * ((self.skills[SkillType.RANGED].level * 3) // 2)

        magic = 0.325 * ((self.skills[SkillType.MAGIC].level * 3) // 2)

        return int(base + max(melee, ranged, magic))

    def update_combat_stats(self) -> None:
        """Update combat stats based on equipment"""
        for stat in self.combat_stats:
            self.combat_stats[stat] = self.equipment.get_bonus(stat)
