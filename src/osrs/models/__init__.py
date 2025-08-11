"""OSRS models module."""
from dataclasses import dataclass
from typing import Dict

from ..core.constants import SkillType, SkillLevel as Skill


@dataclass
class Player:
    id: int
    name: str
    skills: Dict[SkillType, Skill]

    @property
    def total_level(self) -> int:
        return sum(s.level for s in self.skills.values())


from .item import Item, ItemType, ItemRequirements
from .equipment import Equipment, InventoryItem

__all__ = [
    "Player",
    "Item",
    "ItemType",
    "ItemRequirements",
    "Equipment",
    "InventoryItem",
    "SkillType",
    "Skill",
]
