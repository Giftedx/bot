"""OSRS models module."""
from dataclasses import dataclass
from typing import Dict


# Placeholder definitions for SkillType and SkillLevel (Skill)
from enum import Enum

class SkillType(Enum):
    ATTACK = "Attack"
    DEFENCE = "Defence"
    STRENGTH = "Strength"
    HITPOINTS = "Hitpoints"
    # Add other skills as needed

@dataclass
class Skill:
    level: int



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
