"""OSRS models module."""
from .user import User
from .item import Item, ItemType, ItemRequirements
from .equipment import Equipment, InventoryItem
from dataclasses import dataclass, field
from typing import Dict
from ..core.constants import SkillType


@dataclass
class Skill:
    type: SkillType
    level: int = 1
    xp: int = 0


@dataclass
class Player:
    id: int
    name: str
    skills: Dict[SkillType, Skill] = field(default_factory=dict)
    inventory: Dict[str, int] = field(default_factory=dict)
    quest_progress: Dict[int, str] = field(default_factory=dict)
    completed_achievements: list[int] = field(default_factory=list)

    def get_combat_level(self) -> int:
        # Simplified combat level based on key skills
        atk = self.skills.get(SkillType.ATTACK, Skill(SkillType.ATTACK)).level
        strn = self.skills.get(SkillType.STRENGTH, Skill(SkillType.STRENGTH)).level
        defn = self.skills.get(SkillType.DEFENCE, Skill(SkillType.DEFENCE)).level
        hp = self.skills.get(SkillType.HITPOINTS, Skill(SkillType.HITPOINTS, level=10)).level
        prayer = self.skills.get(SkillType.PRAYER, Skill(SkillType.PRAYER)).level
        magic = self.skills.get(SkillType.MAGIC, Skill(SkillType.MAGIC)).level
        ranged = self.skills.get(SkillType.RANGED, Skill(SkillType.RANGED)).level
        base = 0.25 * (defn + hp + (prayer // 2))
        melee = 0.325 * (atk + strn)
        range_val = 0.325 * ((ranged // 2) + ranged)
        mage = 0.325 * ((magic // 2) + magic)
        return int(base + max(melee, range_val, mage))

    def add_item_to_inventory(self, item_name: str, qty: int = 1) -> None:
        self.inventory[item_name] = self.inventory.get(item_name, 0) + qty

    def has_item_in_inventory(self, item_name: str, qty: int = 1) -> bool:
        return self.inventory.get(item_name, 0) >= qty


__all__ = ["User", "Item", "ItemType", "ItemRequirements", "Equipment", "InventoryItem"]
__all__ += ["Player", "Skill", "SkillType"]
