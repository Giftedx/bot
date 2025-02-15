"""OSRS skills implementation."""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
import random
import math

class SkillType(Enum):
    """OSRS skill types."""
    ATTACK = auto()
    DEFENCE = auto()
    STRENGTH = auto()
    HITPOINTS = auto()
    RANGED = auto()
    PRAYER = auto()
    MAGIC = auto()
    COOKING = auto()
    WOODCUTTING = auto()
    FLETCHING = auto()
    FISHING = auto()
    FIREMAKING = auto()
    CRAFTING = auto()
    SMITHING = auto()
    MINING = auto()
    HERBLORE = auto()
    AGILITY = auto()
    THIEVING = auto()
    SLAYER = auto()
    FARMING = auto()
    RUNECRAFTING = auto()
    HUNTER = auto()
    CONSTRUCTION = auto()

@dataclass
class SkillLevel:
    """Represents a skill's level and experience."""
    level: int = 1
    xp: int = 0

    def __post_init__(self):
        """Validate and initialize skill level and XP."""
        if self.level < 1:
            self.level = 1
        if self.level > 99:
            self.level = 99
        if self.xp < 0:
            self.xp = 0

    @property
    def virtual_level(self) -> int:
        """Calculate virtual level based on XP (can exceed 99)."""
        level = 1
        xp = self.xp
        while xp >= self._xp_for_level(level + 1):
            level += 1
        return level

    @staticmethod
    def _xp_for_level(level: int) -> int:
        """Calculate XP required for a given level using OSRS formula."""
        total = 0
        for i in range(1, level):
            total += int(i + 300 * (2 ** (i / 7.0)))
        return int(total / 4)

    def add_xp(self, xp: int) -> None:
        """Add XP to the skill and update level if necessary."""
        if xp <= 0:
            return

        self.xp += xp
        new_level = 1

        while (new_level < 99 and 
               self.xp >= self._xp_for_level(new_level + 1)):
            new_level += 1

        self.level = new_level

    def meets_requirement(self, required_level: int) -> bool:
        """Check if current level meets a requirement."""
        return self.level >= required_level

    def boost(self, amount: int) -> int:
        """Calculate boosted level, capped at 99."""
        boosted = self.level + amount
        return min(max(boosted, 1), 99)

class SkillManager:
    """Manages skill levels and training for a player"""
    
    def __init__(self):
        self.skills: Dict[SkillType, SkillLevel] = {
            skill_type: SkillLevel() for skill_type in SkillType
        }
        # Start with 10 HP
        self.skills[SkillType.HITPOINTS].level = 10
        self.skills[SkillType.HITPOINTS].xp = SkillLevel._xp_for_level(10)
    
    def get_level(self, skill: SkillType) -> int:
        """Get the current level of a skill"""
        return self.skills[skill].level
    
    def get_xp(self, skill: SkillType) -> int:
        """Get the current XP in a skill"""
        return self.skills[skill].xp
    
    def add_xp(self, skill: SkillType, xp: int) -> None:
        """
        Add XP to a skill
        """
        self.skills[skill].add_xp(xp)
    
    def get_total_level(self) -> int:
        """Get the total level across all skills"""
        return sum(skill.level for skill in self.skills.values())
    
    def get_total_xp(self) -> int:
        """Get the total XP across all skills"""
        return sum(skill.xp for skill in self.skills.values())
    
    def get_combat_level(self) -> int:
        """Calculate combat level using OSRS formula"""
        base = 0.25 * (
            self.get_level(SkillType.DEFENCE) +
            self.get_level(SkillType.HITPOINTS) +
            math.floor(self.get_level(SkillType.PRAYER) / 2)
        )
        
        melee = 0.325 * (
            self.get_level(SkillType.ATTACK) +
            self.get_level(SkillType.STRENGTH)
        )
        
        ranged = 0.325 * (
            math.floor(3 * self.get_level(SkillType.RANGED) / 2)
        )
        
        magic = 0.325 * (
            math.floor(3 * self.get_level(SkillType.MAGIC) / 2)
        )
        
        return math.floor(base + max(melee, ranged, magic))

    def meets_requirement(self, skill: SkillType, required_level: int) -> bool:
        """Check if the player meets a skill level requirement"""
        return self.get_level(skill) >= required_level 