"""OSRS game mechanics and formulas."""
from math import floor
from typing import Dict, Optional

from ..models import SkillType


def calculate_combat_level(skills: Dict[SkillType, int]) -> int:
    """
    Calculate combat level using official OSRS formula.
    
    Args:
        skills: Dictionary of skill levels keyed by SkillType
    
    Returns:
        int: Combat level (1-126)
    """
    base = 0.25 * (
        skills[SkillType.DEFENCE] +
        skills[SkillType.HITPOINTS] +
        floor(skills[SkillType.PRAYER] / 2)
    )
    
    melee = 0.325 * (
        skills[SkillType.ATTACK] +
        skills[SkillType.STRENGTH]
    )
    
    ranged = 0.325 * floor(
        (skills[SkillType.RANGED] * 3) / 2
    )
    
    magic = 0.325 * floor(
        (skills[SkillType.MAGIC] * 3) / 2
    )
    
    return floor(base + max(melee, ranged, magic))


def calculate_max_hit(
    strength_level: int,
    equipment_bonus: int,
    prayer_bonus: float = 1.0,
    other_bonus: float = 1.0
) -> int:
    """
    Calculate maximum melee hit using OSRS formula.
    
    Args:
        strength_level: Base strength level
        equipment_bonus: Total strength bonus from equipment
        prayer_bonus: Multiplier from active prayers
        other_bonus: Other multipliers (void, slayer helm, etc)
    
    Returns:
        int: Maximum possible hit
    """
    effective_level = floor(
        strength_level * prayer_bonus * other_bonus
    )
    base = floor(0.5 + effective_level * (equipment_bonus + 64) / 640)
    return floor(base * other_bonus)


def calculate_success_chance(
    skill_type: SkillType,
    skill_level: int,
    required_level: int,
    tool_bonus: int = 0
) -> float:
    """
    Calculate success chance for gathering skills.
    
    Args:
        skill_type: The type of skill being used
        skill_level: Current skill level
        required_level: Level required for the resource
        tool_bonus: Bonus from equipped tools
    
    Returns:
        float: Success chance between 0 and 1
    """
    # Base chance scales with level difference
    level_diff = skill_level - required_level
    base_chance = 0.3 + (level_diff * 0.01)
    
    # Apply tool bonus
    chance = base_chance + (tool_bonus * 0.05)
    
    # Clamp between 10% and 90%
    return max(0.1, min(0.9, chance))


def calculate_xp_rate(
    skill_type: SkillType,
    base_xp: float,
    skill_level: int,
    modifiers: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate XP gain rate accounting for bonuses.
    
    Args:
        skill_type: The type of skill
        base_xp: Base XP for the action
        skill_level: Current skill level
        modifiers: Dict of XP modifiers (outfit, events, etc)
    
    Returns:
        float: Modified XP amount
    """
    if modifiers is None:
        modifiers = {}
    
    # Apply all modifiers multiplicatively
    xp = base_xp
    for modifier in modifiers.values():
        xp *= modifier
        
    return floor(xp)


def xp_to_level(xp: int) -> int:
    """
    Convert XP to level using OSRS formula.
    
    Args:
        xp: Total XP in skill
        
    Returns:
        int: Corresponding level (1-99)
    """
    for level in range(1, 100):
        if xp < level_to_xp(level):
            return level - 1
    return 99


def level_to_xp(level: int) -> int:
    """
    Calculate XP required for a level using OSRS formula.
    
    Args:
        level: Target level
        
    Returns:
        int: XP required
    """
    total = 0
    for i in range(1, level):
        total += floor(i + 300 * pow(2, i / 7.0))
    return floor(total / 4)
