"""Skill system implementing exact OSRS skill mechanics."""

import math
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class Skill(Enum):
    """Skills available in OSRS."""
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
class SkillLevel:
    """Represents a skill's level and experience."""
    level: int
    experience: float
    
class SkillSystem:
    """Implements OSRS skill mechanics."""
    
    # Constants from OSRS
    MAX_LEVEL = 99
    MAX_EXPERIENCE = 200_000_000
    GAME_TICK = 0.6  # seconds
    
    # Experience table (level: experience required)
    XP_TABLE = {
        1: 0,
        2: 83,
        3: 174,
        4: 276,
        5: 388,
        6: 512,
        7: 650,
        8: 801,
        9: 969,
        10: 1154,
        # ... continues to 99
        99: 13_034_431
    }
    
    def __init__(self):
        """Initialize the skill system."""
        # Complete the XP table
        self._complete_xp_table()
        
    def _complete_xp_table(self):
        """Fill in missing XP table values using OSRS formula."""
        for level in range(11, 100):
            if level not in self.XP_TABLE:
                points = math.floor(level - 1 + 300 * 2**((level - 1) / 7))
                self.XP_TABLE[level] = math.floor(points / 4)
                
    def get_level_for_xp(self, xp: float) -> int:
        """Get the level for a given amount of experience.
        
        Args:
            xp: The amount of experience.
            
        Returns:
            The corresponding level (1-99).
        """
        for level in range(99, 0, -1):
            if xp >= self.XP_TABLE[level]:
                return level
        return 1
        
    def get_xp_for_level(self, level: int) -> float:
        """Get the minimum experience required for a level.
        
        Args:
            level: The target level (1-99).
            
        Returns:
            The required experience.
            
        Raises:
            ValueError: If level is not between 1 and 99.
        """
        if not 1 <= level <= 99:
            raise ValueError("Level must be between 1 and 99")
        return float(self.XP_TABLE[level])
        
    def calculate_mining_success(self,
                               level: int,
                               rock_level: int,
                               pickaxe_bonus: int) -> float:
        """Calculate mining success chance using OSRS formula.
        
        Args:
            level: Mining level
            rock_level: Required level for rock
            pickaxe_bonus: Mining bonus from pickaxe
            
        Returns:
            Success chance (0-1)
        """
        effective_level = level + 3 + pickaxe_bonus  # Include invisible +3 boost
        chance = (effective_level - rock_level) / 50
        return min(0.95, max(0.01, chance))
        
    def calculate_woodcutting_success(self,
                                    level: int,
                                    tree_level: int,
                                    axe_bonus: int) -> float:
        """Calculate woodcutting success chance using OSRS formula.
        
        Args:
            level: Woodcutting level
            tree_level: Required level for tree
            axe_bonus: Woodcutting bonus from axe
            
        Returns:
            Success chance (0-1)
        """
        effective_level = level + 8 + axe_bonus
        chance = (effective_level - tree_level) / 40
        return min(0.95, max(0.01, chance))
        
    def calculate_fishing_success(self,
                                level: int,
                                spot_level: int,
                                tool_bonus: int) -> float:
        """Calculate fishing success chance using OSRS formula.
        
        Args:
            level: Fishing level
            spot_level: Required level for fishing spot
            tool_bonus: Fishing bonus from tool
            
        Returns:
            Success chance (0-1)
        """
        effective_level = level + tool_bonus
        chance = (effective_level - spot_level) / 45
        return min(0.95, max(0.01, chance))
        
    def calculate_thieving_success(self,
                                 level: int,
                                 target_level: int,
                                 glove_bonus: int = 0) -> float:
        """Calculate thieving success chance using OSRS formula.
        
        Args:
            level: Thieving level
            target_level: Required level for target
            glove_bonus: Success bonus from gloves
            
        Returns:
            Success chance (0-1)
        """
        effective_level = level + glove_bonus
        chance = (effective_level - target_level) / 35
        return min(0.95, max(0.01, chance))
        
    def calculate_agility_success(self,
                                level: int,
                                obstacle_level: int) -> float:
        """Calculate agility success chance using OSRS formula.
        
        Args:
            level: Agility level
            obstacle_level: Required level for obstacle
            
        Returns:
            Success chance (0-1)
        """
        chance = (level - obstacle_level) / 30
        return min(1.0, max(0.2, chance))
        
    def calculate_crafting_speed(self,
                               level: int,
                               item_level: int) -> float:
        """Calculate crafting actions per minute using OSRS formula.
        
        Args:
            level: Crafting level
            item_level: Required level for item
            
        Returns:
            Actions per minute
        """
        base_speed = 20  # Base actions per minute
        speed_bonus = (level - item_level) / 5
        return base_speed + speed_bonus
        
    def calculate_cooking_success(self,
                                level: int,
                                food_level: int,
                                gauntlets_bonus: bool = False) -> float:
        """Calculate cooking success chance using OSRS formula.
        
        Args:
            level: Cooking level
            food_level: Required level for food
            gauntlets_bonus: Whether cooking gauntlets are worn
            
        Returns:
            Success chance (0-1)
        """
        effective_level = level + (6 if gauntlets_bonus else 0)
        chance = (effective_level - food_level) / 25
        return min(0.95, max(0.01, chance))
        
    def calculate_herblore_success(self,
                                 level: int,
                                 potion_level: int) -> float:
        """Calculate herblore success chance using OSRS formula.
        
        Args:
            level: Herblore level
            potion_level: Required level for potion
            
        Returns:
            Success chance (0-1)
        """
        chance = (level - potion_level) / 20
        return min(0.98, max(0.7, chance))
        
    def calculate_fletching_speed(self,
                                level: int,
                                item_level: int) -> float:
        """Calculate fletching actions per minute using OSRS formula.
        
        Args:
            level: Fletching level
            item_level: Required level for item
            
        Returns:
            Actions per minute
        """
        base_speed = 25  # Base actions per minute
        speed_bonus = (level - item_level) / 4
        return base_speed + speed_bonus
        
    def calculate_smithing_speed(self,
                               level: int,
                               item_level: int) -> float:
        """Calculate smithing actions per minute using OSRS formula.
        
        Args:
            level: Smithing level
            item_level: Required level for item
            
        Returns:
            Actions per minute
        """
        base_speed = 15  # Base actions per minute
        speed_bonus = (level - item_level) / 6
        return base_speed + speed_bonus
        
    def calculate_runecraft_multiplier(self,
                                     level: int,
                                     rune_level: int) -> int:
        """Calculate runecraft multiple runes threshold.
        
        Args:
            level: Runecraft level
            rune_level: Required level for rune
            
        Returns:
            Number of runes crafted per essence
        """
        if rune_level >= 50:  # Law runes and above never multiply
            return 1
            
        thresholds = {
            1: 11,   # Air runes
            2: 14,   # Mind runes
            5: 19,   # Water runes
            9: 26,   # Earth runes
            14: 35,  # Fire runes
            20: 46,  # Body runes
            27: 59,  # Cosmic runes
            35: 74,  # Chaos runes
            44: 91,  # Nature runes
        }
        
        multiplier = 1
        threshold = thresholds.get(rune_level, 99)
        
        while level >= threshold and threshold < 99:
            multiplier += 1
            threshold += threshold
            
        return multiplier 