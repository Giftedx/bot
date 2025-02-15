"""Validation utilities for battle system."""

from typing import Any, Dict, List, Optional

from .exceptions import ValidationError
from .interfaces import BattleState, BattleType


def validate_move(move: str, available_moves: List[str]) -> None:
    """Validate a battle move.

    Args:
        move: The move to validate
        available_moves: List of valid moves

    Raises:
        ValidationError: If move is invalid
    """
    if not move or not isinstance(move, str):
        raise ValidationError("Move must be a non-empty string")

    if move not in available_moves:
        raise ValidationError(
            f"Invalid move '{move}'. Available moves: {', '.join(available_moves)}"
        )


def validate_battle_state(battle_state: BattleState) -> None:
    """Validate battle state integrity.

    Args:
        battle_state: The battle state to validate

    Raises:
        ValidationError: If battle state is invalid
    """
    if not battle_state:
        raise ValidationError("Battle state cannot be None")

    if not battle_state.battle_id:
        raise ValidationError("Battle ID is required")

    if not isinstance(battle_state.battle_type, BattleType):
        raise ValidationError("Invalid battle type")

    if not battle_state.challenger_id or not battle_state.opponent_id:
        raise ValidationError("Both challenger and opponent IDs are required")

    if battle_state.challenger_id == battle_state.opponent_id:
        raise ValidationError("Challenger and opponent cannot be the same player")


def validate_stats(stats: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate player/entity stats.

    Args:
        stats: Stats dictionary to validate
        required_fields: List of required stat fields

    Raises:
        ValidationError: If stats are invalid
    """
    if not stats or not isinstance(stats, dict):
        raise ValidationError("Stats must be a non-empty dictionary")

    for field in required_fields:
        if field not in stats:
            raise ValidationError(f"Missing required stat: {field}")

        value = stats[field]
        if not isinstance(value, (int, float)) or value < 0:
            raise ValidationError(
                f"Invalid value for {field}: must be a non-negative number"
            )


def validate_player_turn(battle_state: BattleState, player_id: int) -> None:
    """Validate if it's the player's turn.

    Args:
        battle_state: Current battle state
        player_id: ID of player attempting move

    Raises:
        ValidationError: If not player's turn
    """
    if battle_state.current_turn != player_id:
        raise ValidationError("Not your turn!")


def validate_battle_active(battle_state: BattleState) -> None:
    """Validate battle is still active.

    Args:
        battle_state: Battle state to validate

    Raises:
        ValidationError: If battle is finished
    """
    if battle_state.is_finished:
        raise ValidationError("Battle is already finished")


def validate_resource_cost(
    stats: Dict[str, Any],
    costs: Dict[str, int],
    resource_types: Optional[List[str]] = None,
) -> None:
    """Validate player has sufficient resources for move.

    Args:
        stats: Player stats
        costs: Resource costs dictionary
        resource_types: Optional list of valid resource types

    Raises:
        ValidationError: If insufficient resources
    """
    if not resource_types:
        resource_types = ["hp", "energy", "mana", "stamina"]

    for resource, cost in costs.items():
        if resource not in resource_types:
            raise ValidationError(f"Invalid resource type: {resource}")

        current = stats.get(f"current_{resource}", 0)
        if current < cost:
            raise ValidationError(
                f"Insufficient {resource}: need {cost}, have {current}"
            )


def validate_status_effects(
    stats: Dict[str, Any], move: str, prevented_by: Optional[List[str]] = None
) -> None:
    """Validate status effects don't prevent move.

    Args:
        stats: Player stats
        move: Attempted move
        prevented_by: Optional list of preventing status effects

    Raises:
        ValidationError: If move is prevented
    """
    if not prevented_by:
        prevented_by = ["frozen", "paralyzed", "stunned", "sleeping"]

    status_effects = stats.get("status_effects", [])
    for status in status_effects:
        if status in prevented_by:
            raise ValidationError(f"Cannot use {move} while {status}")
