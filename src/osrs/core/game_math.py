"""OSRS game mathematics and formulas."""
from math import floor
from typing import Dict, Tuple, Optional

from .constants import SkillType


def calculate_combat_level(levels: Dict[str, int]) -> int:
    """Calculate combat level using OSRS formula."""
    base = 0.25 * (levels["defence"] + levels["hitpoints"] + floor(levels["prayer"] / 2))

    melee = 0.325 * (levels["attack"] + levels["strength"])
    ranged = 0.325 * (floor(3 * levels["ranged"] / 2))
    magic = 0.325 * (floor(3 * levels["magic"] / 2))

    return floor(base + max(melee, ranged, magic))


def calculate_max_hit(
    strength_level: int,
    equipment_bonus: int,
    prayer_bonus: float = 1.0,
    other_bonus: float = 1.0,
    style_bonus: int = 0,
) -> int:
    """Calculate maximum melee hit using OSRS formula."""
    effective_str = floor(((strength_level + style_bonus + 8) * prayer_bonus) * other_bonus)
    return floor(0.5 + effective_str * (equipment_bonus + 64) / 640)


def calculate_hit_chance(
    attack_level: int,
    equipment_bonus: int,
    target_defence: int,
    target_bonus: int,
    prayer_bonus: float = 1.0,
    other_bonus: float = 1.0,
    style_bonus: int = 0,
) -> float:
    """Calculate hit chance using OSRS accuracy formula."""
    effective_atk = floor(((attack_level + style_bonus + 8) * prayer_bonus) * other_bonus)
    attack_roll = effective_atk * (equipment_bonus + 64)

    effective_def = floor(target_defence + 8)
    defence_roll = effective_def * (target_bonus + 64)

    if attack_roll > defence_roll:
        return 1 - (defence_roll + 2) / (2 * (attack_roll + 1))
    else:
        return attack_roll / (2 * (defence_roll + 1))


def calculate_xp_for_level(level: int) -> int:
    """Calculate XP required for a given level."""
    if level < 1 or level > 99:
        raise ValueError("Level must be between 1 and 99")

    total = 0
    for i in range(1, level):
        total += floor(i + 300 * pow(2, i / 7))
    return floor(total / 4)


def calculate_level_for_xp(xp: int) -> int:
    """Calculate level for given XP amount."""
    for level in range(1, 100):
        if xp < calculate_xp_for_level(level):
            return level - 1
    return 99


def calculate_prayer_drain(active_prayers: Dict[str, bool], prayer_bonus: int = 0) -> float:
    """Calculate prayer point drain rate per tick."""
    base_drain = 0
    for prayer, active in active_prayers.items():
        if active:
            if prayer == "protect_melee":
                base_drain += 1
            elif prayer == "protect_ranged":
                base_drain += 1
            elif prayer == "protect_magic":
                base_drain += 1
            elif prayer == "piety":
                base_drain += 4
            elif prayer == "rigour":
                base_drain += 4
            elif prayer == "augury":
                base_drain += 4

    if base_drain == 0:
        return 0

    drain_rate = base_drain * (1 + prayer_bonus / 30)
    return max(0.1, drain_rate)  # Minimum drain of 0.1 points per tick


def calculate_special_attack_damage(
    base_damage: int, spec_multiplier: float, accuracy_multiplier: float = 1.0
) -> Tuple[int, bool]:
    """Calculate special attack damage and accuracy."""
    # Special attack accuracy roll
    accuracy_roll = accuracy_multiplier >= 1.0 or random.random() < accuracy_multiplier

    if not accuracy_roll:
        return 0, False

    damage = floor(base_damage * spec_multiplier)
    return damage, True


def calculate_experience_rate(base_rate: int, level: int, bonus_multiplier: float = 1.0) -> float:
    """Calculate experience rate per action."""
    level_scaling = 1 + (level - 1) / 50  # 2% increase per level
    return base_rate * level_scaling * bonus_multiplier


def calculate_success_chance(
    skill_type: SkillType, skill_level: int, required_level: int, tool_bonus: int = 0
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
    modifiers: Optional[Dict[str, float]] = None,
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
