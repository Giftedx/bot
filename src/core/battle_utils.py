"""Utility functions for battle system."""

import random
from typing import Any, Dict, List, Optional, Tuple

from .battle_config import STAT_STAGE_MULTIPLIERS
from .exceptions import ValidationError
from .models import BattleMove, BattleState, StatusEffect


def calculate_stat_multiplier(stage: int) -> float:
    """Calculate stat multiplier for a given stage.

    Args:
        stage: Current stat stage (-6 to +6)

    Returns:
        float: Stat multiplier
    """
    stage = max(-6, min(6, stage))
    return STAT_STAGE_MULTIPLIERS[stage]


def apply_stat_changes(
    stats: Dict[str, Any], changes: Dict[str, int]
) -> Tuple[Dict[str, Any], List[str]]:
    """Apply stat stage changes.

    Args:
        stats: Current stats
        changes: Stat changes to apply

    Returns:
        Tuple[Dict[str, Any], List[str]]: Modified stats and messages
    """
    modified = stats.copy()
    messages = []

    for stat, change in changes.items():
        current = modified.get(f"{stat}_stage", 0)
        new_stage = max(-6, min(6, current + change))
        modified[f"{stat}_stage"] = new_stage

        if new_stage != current:
            if change > 0:
                messages.append(f"{stat.title()} rose!")
            else:
                messages.append(f"{stat.title()} fell!")

        # Apply the stat modifier
        base_value = modified[stat]
        modified[stat] = int(base_value * calculate_stat_multiplier(new_stage))

    return modified, messages


def calculate_type_effectiveness(move_type: str, defender_types: List[str]) -> float:
    """Calculate type effectiveness multiplier.

    Args:
        move_type: Type of the move
        defender_types: Types of the defender

    Returns:
        float: Effectiveness multiplier
    """
    # Implementation would include type chart logic
    return 1.0


def calculate_critical_hit(
    attacker_stats: Dict[str, Any], move: BattleMove
) -> Tuple[bool, float]:
    """Calculate if attack is critical hit.

    Args:
        attacker_stats: Attacker's stats
        move: Move being used

    Returns:
        Tuple[bool, float]: Is critical hit and multiplier
    """
    base_crit_rate = attacker_stats.get("crit_rate", 0.0625)
    move_crit_bonus = getattr(move, "crit_bonus", 0)

    crit_chance = min(base_crit_rate + move_crit_bonus, 1.0)
    is_crit = random.random() < crit_chance

    return is_crit, 1.5 if is_crit else 1.0


def apply_status_effect(
    stats: Dict[str, Any], effect: StatusEffect
) -> Tuple[Dict[str, Any], str]:
    """Apply a status effect to stats.

    Args:
        stats: Current stats
        effect: Status effect to apply

    Returns:
        Tuple[Dict[str, Any], str]: Modified stats and message
    """
    modified = stats.copy()
    message = f"{effect.name} was applied!"

    if effect.stat_modifiers:
        for stat, modifier in effect.stat_modifiers.items():
            if stat in modified:
                modified[stat] = int(modified[stat] * modifier)
                message += f"\n{stat.title()} was affected!"

    current_effects = modified.get("status_effects", [])
    if len(current_effects) >= 3:
        raise ValidationError("Maximum status effects reached")

    current_effects.append(effect)
    modified["status_effects"] = current_effects

    return modified, message


def check_move_requirements(stats: Dict[str, Any], move: BattleMove) -> Optional[str]:
    """Check if move requirements are met.

    Args:
        stats: Current stats
        move: Move to check

    Returns:
        Optional[str]: Error message if requirements not met
    """
    if move.energy_cost:
        current = stats.get("current_energy", 0)
        if current < move.energy_cost:
            return f"Need {move.energy_cost} energy, have {current}"

    if move.hp_cost:
        current = stats.get("current_hp", 0)
        if current < move.hp_cost:
            return f"Need {move.hp_cost} HP, have {current}"

    if move.resource_cost:
        for resource, cost in move.resource_cost.items():
            current = stats.get(f"current_{resource}", 0)
            if current < cost:
                return f"Need {cost} {resource}, have {current}"

    return None


def calculate_accuracy(
    move: BattleMove, attacker_stats: Dict[str, Any], defender_stats: Dict[str, Any]
) -> bool:
    """Calculate if move hits.

    Args:
        move: Move being used
        attacker_stats: Attacker's stats
        defender_stats: Defender's stats

    Returns:
        bool: Whether move hits
    """
    if move.accuracy is None:
        return True

    accuracy_stage = attacker_stats.get("accuracy_stage", 0)
    evasion_stage = defender_stats.get("evasion_stage", 0)

    accuracy_mult = calculate_stat_multiplier(accuracy_stage)
    evasion_mult = calculate_stat_multiplier(evasion_stage)

    final_accuracy = move.accuracy * accuracy_mult / evasion_mult

    return random.random() < final_accuracy


def format_battle_message(template: str, **kwargs: Any) -> str:
    """Format battle message with variables.

    Args:
        template: Message template
        **kwargs: Variables to format

    Returns:
        str: Formatted message
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        return f"Error formatting message: missing {e}"
    except Exception as e:
        return f"Error formatting message: {e}"


def get_battle_rewards(
    battle_state: BattleState, winner_id: Optional[int]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Calculate battle rewards.

    Args:
        battle_state: Final battle state
        winner_id: ID of winner if any

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any]]: Winner and loser rewards
    """
    from .battle_config import DEFAULT_REWARD_CONFIGS

    config = DEFAULT_REWARD_CONFIGS[battle_state.battle_type]

    if winner_id:
        winner_reward = {
            "xp": int(config.base_xp * config.win_multiplier),
            "coins": int(config.base_coins * config.win_multiplier),
        }

        loser_reward = {
            "xp": int(config.base_xp * config.loss_multiplier),
            "coins": int(config.base_coins * config.loss_multiplier),
        }
    else:
        # Draw
        winner_reward = loser_reward = {
            "xp": int(config.base_xp * 0.75),
            "coins": int(config.base_coins * 0.75),
        }

    return winner_reward, loser_reward
