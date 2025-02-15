"""OSRS game mechanics and formulas."""

from math import floor
from typing import Dict, Optional

from .models import SkillType


def calculate_max_hit(
    strength_level: int,
    equipment_bonus: int,
    prayer_bonus: float = 1.0,
    other_bonus: float = 1.0,
) -> int:
    """Calculate maximum melee hit using OSRS formula."""
    effective = floor(strength_level * prayer_bonus)
    base = floor(
        1.3
        + (effective / 10)
        + (equipment_bonus / 80)
        + ((effective * equipment_bonus) / 640)
    )
    return floor(base * other_bonus)


def calculate_hit_chance(
    attack_level: int, equipment_bonus: int, target_defence: int, target_bonus: int
) -> float:
    """Calculate hit chance using OSRS accuracy formula."""
    attack_roll = attack_level * (equipment_bonus + 64)
    defence_roll = target_defence * (target_bonus + 64)

    if attack_roll > defence_roll:
        return 1 - ((defence_roll + 2) / (2 * (attack_roll + 1)))
    else:
        return attack_roll / (2 * (defence_roll + 1))


def calculate_success_chance(
    skill_type: SkillType, skill_level: int, required_level: int, tool_bonus: int = 0
) -> float:
    """Calculate success chance for gathering skills."""
    if skill_level < required_level:
        return 0.0

    base = (skill_level - required_level) * 2
    bonus = tool_bonus * 1.5
    chance = (base + bonus) / 100

    return min(max(chance, 0.0), 0.95)  # Cap between 0-95%


def calculate_xp_rate(
    skill_type: SkillType,
    base_xp: float,
    skill_level: int,
    modifiers: Optional[Dict[str, float]] = None,
) -> float:
    """Calculate XP rate for an action."""
    if modifiers is None:
        modifiers = {}

    # Apply skill-specific scaling
    if skill_type in [SkillType.ATTACK, SkillType.STRENGTH, SkillType.DEFENCE]:
        base_xp *= 4.0  # Combat skills get 4x XP
    elif skill_type == SkillType.HITPOINTS:
        base_xp *= 1.33  # Hitpoints gets 1.33x XP

    # Apply level scaling (higher levels = slightly better XP)
    level_bonus = 1.0 + (skill_level / 200)  # +0.5% per level
    base_xp *= level_bonus

    # Apply modifiers
    for modifier in modifiers.values():
        base_xp *= modifier

    return base_xp


def calculate_drain_rate(
    prayer_points: int, active_prayers: list[str], prayer_bonus: int
) -> float:
    """Calculate prayer point drain rate per tick."""
    if not active_prayers:
        return 0.0

    base_drain = sum(PRAYER_DRAIN_RATES.get(prayer, 0) for prayer in active_prayers)
    bonus_mult = 1 + (prayer_bonus / 30)  # Each +1 prayer bonus = +3.33% duration

    return base_drain / bonus_mult


# Prayer drain rates per game tick (0.6 seconds)
PRAYER_DRAIN_RATES = {
    "protect_melee": 1,
    "protect_ranged": 1,
    "protect_magic": 1,
    "piety": 4,
    "rigour": 4,
    "augury": 4,
    "eagle_eye": 2,
    "mystic_might": 2,
    "incredible_reflexes": 2,
    "ultimate_strength": 2,
    "steel_skin": 2,
}
