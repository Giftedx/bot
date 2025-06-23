"""Base implementation of battle system."""

from abc import ABC
from typing import Any, Dict, List, Optional, Tuple

from .exceptions import (
    InvalidMoveError,
    ResourceError,
    StatusEffectError,
    ValidationError,
)
from .interfaces import IBattleSystem
from .models import BattleMove, BattleState, StatusEffect
from .validators import (
    validate_battle_active,
    validate_battle_state,
    validate_move,
    validate_move_resources,
    validate_player_turn,
    validate_status_effects,
)


class BaseBattleSystem(IBattleSystem, ABC):
    """Abstract base implementation of battle system."""

    def __init__(self) -> None:
        self.stat_modifiers = {
            -6: 0.25,  # -6 stages = 25% of original stat
            -5: 0.29,
            -4: 0.33,
            -3: 0.40,
            -2: 0.50,
            -1: 0.67,
            0: 1.0,  # No modification
            1: 1.5,
            2: 2.0,
            3: 2.5,
            4: 3.0,
            5: 3.5,
            6: 4.0,  # +6 stages = 400% of original stat
        }

    def process_turn(self, battle_state: BattleState, move_name: str) -> Dict[str, Any]:
        """Process a turn and return the turn results."""
        # Validate battle state
        validate_battle_state(battle_state)
        validate_battle_active(battle_state)

        # Get player stats
        attacker_stats = self._get_player_stats(battle_state)
        defender_stats = self._get_opponent_stats(battle_state)

        # Get and validate move
        available_moves = self.get_available_moves(battle_state, battle_state.current_turn)
        move = self._get_move_by_name(move_name, available_moves)
        validate_move(move, available_moves)

        # Validate resources and status
        validate_move_resources(move, attacker_stats)
        validate_status_effects(move, attacker_stats)

        # Calculate and apply damage
        damage, effect_msg = self.calculate_damage(move, attacker_stats, defender_stats)

        # Apply resource costs
        attacker_stats = self._apply_resource_costs(attacker_stats, move)

        # Apply move effects
        if move.status_effects:
            defender_stats, status_msg = self.apply_status_effects(
                defender_stats, move.status_effects
            )
            effect_msg = f"{effect_msg}\n{status_msg}" if status_msg else effect_msg

        # Update battle state
        battle_state.battle_data.update(
            {"attacker_stats": attacker_stats, "defender_stats": defender_stats}
        )

        return {
            "damage": damage,
            "message": effect_msg,
            "attacker_stats": attacker_stats,
            "defender_stats": defender_stats,
        }

    def apply_status_effects(
        self, stats: Dict[str, Any], effects: List[StatusEffect]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Apply status effects and return modified stats + messages."""
        messages = []
        modified_stats = stats.copy()

        for effect in effects:
            if effect.stat_modifiers:
                for stat, modifier in effect.stat_modifiers.items():
                    if stat in modified_stats:
                        modified_stats[stat] = int(modified_stats[stat] * modifier)
                        messages.append(f"{effect.name} affected {stat}!")

            if effect.dot_damage:
                messages.append(f"{effect.name} will deal damage over time!")

            if effect.prevents_moves:
                messages.append(f"{effect.name} may prevent moves!")

            current_effects = modified_stats.get("status_effects", [])
            current_effects.append(effect)
            modified_stats["status_effects"] = current_effects

        return modified_stats, messages

    def _get_player_stats(self, battle_state: BattleState) -> Dict[str, Any]:
        """Get stats for current player."""
        return (
            battle_state.battle_data.get("challenger_stats", {})
            if battle_state.current_turn == battle_state.challenger_id
            else battle_state.battle_data.get("opponent_stats", {})
        )

    def _get_opponent_stats(self, battle_state: BattleState) -> Dict[str, Any]:
        """Get stats for opponent."""
        return (
            battle_state.battle_data.get("opponent_stats", {})
            if battle_state.current_turn == battle_state.challenger_id
            else battle_state.battle_data.get("challenger_stats", {})
        )

    def _get_move_by_name(self, move_name: str, available_moves: List[BattleMove]) -> BattleMove:
        """Get move object by name."""
        for move in available_moves:
            if move.name.lower() == move_name.lower():
                return move
        raise InvalidMoveError(f"Move not found: {move_name}")

    def _apply_resource_costs(self, stats: Dict[str, Any], move: BattleMove) -> Dict[str, Any]:
        """Apply move resource costs to stats."""
        modified = stats.copy()

        if move.energy_cost:
            current = modified.get("current_energy", 0)
            if current < move.energy_cost:
                raise ResourceError("Insufficient energy")
            modified["current_energy"] = current - move.energy_cost

        if move.hp_cost:
            current = modified.get("current_hp", 0)
            if current < move.hp_cost:
                raise ResourceError("Insufficient HP")
            modified["current_hp"] = current - move.hp_cost

        if move.resource_cost:
            for resource, cost in move.resource_cost.items():
                current = modified.get(f"current_{resource}", 0)
                if current < cost:
                    raise ResourceError(f"Insufficient {resource}")
                modified[f"current_{resource}"] = current - cost

        return modified

    def apply_stat_changes(
        self, stats: Dict[str, Any], changes: Dict[str, int]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Apply stat stage changes and return modified stats + messages."""
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
            modified[stat] = int(base_value * self.stat_modifiers[new_stage])

        return modified, messages
