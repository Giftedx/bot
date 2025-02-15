"""Base battle system interface and shared functionality."""

import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, TypeVar

from src.core.battle_manager import BattleState, BattleType

T = TypeVar("T", bound="BaseBattleSystem")


class BaseBattleSystem(ABC):
    """Abstract base class for battle systems."""

    def __init__(self, battle_type: BattleType) -> None:
        self.battle_type = battle_type
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

    @abstractmethod
    def calculate_damage(
        self, move: str, attacker_stats: Dict[str, Any], defender_stats: Dict[str, Any]
    ) -> Tuple[int, str]:
        """Calculate damage and return amount + effect message."""

    @abstractmethod
    def process_turn(self, battle_state: BattleState, move: str) -> Dict[str, Any]:
        """Process a turn and return the turn results."""

    @abstractmethod
    def is_valid_move(
        self, battle_state: BattleState, move: str, player_id: int
    ) -> bool:
        """Validate if a move is legal for the current state."""

    @abstractmethod
    def get_available_moves(
        self, battle_state: BattleState, player_id: int
    ) -> List[str]:
        """Get list of available moves for a player."""

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

    def check_turn_order(
        self, attacker: Dict[str, Any], defender: Dict[str, Any]
    ) -> bool:
        """Determine if attacker should move first based on speed/priority."""
        attacker_speed = attacker.get("speed", 0)
        defender_speed = defender.get("speed", 0)

        # Priority moves take precedence
        attacker_priority = attacker.get("move_priority", 0)
        defender_priority = defender.get("move_priority", 0)

        if attacker_priority != defender_priority:
            return attacker_priority > defender_priority

        # Apply status effects that modify speed
        for status in attacker.get("status_effects", []):
            if "speed_mod" in status:
                attacker_speed = int(attacker_speed * status["speed_mod"])

        for status in defender.get("status_effects", []):
            if "speed_mod" in status:
                defender_speed = int(defender_speed * status["speed_mod"])

        # Break speed ties randomly
        if attacker_speed == defender_speed:
            return random.random() < 0.5

        return attacker_speed > defender_speed

    def can_use_move(
        self, attacker: Dict[str, Any], move: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Check if a move can be used considering status effects and resources."""
        # Check for status effects that prevent moves
        for status in attacker.get("status_effects", []):
            if status.get("prevents_moves", False):
                return False, f"Cannot move due to {status['name']}!"

        # Check resource costs
        if "energy_cost" in move:
            if attacker.get("current_energy", 0) < move["energy_cost"]:
                return False, "Not enough energy!"

        if "hp_cost" in move:
            if attacker.get("current_hp", 0) < move["hp_cost"]:
                return False, "Not enough HP!"

        if "resource_cost" in move:
            for resource, cost in move["resource_cost"].items():
                if attacker.get(f"current_{resource}", 0) < cost:
                    return False, f"Not enough {resource}!"

        return True, None

    def apply_end_turn_effects(
        self, battle_state: BattleState
    ) -> Tuple[Dict[str, Any], str]:
        """Apply effects that trigger at end of turn."""
        messages = []
        battle_data = battle_state.battle_data.copy()

        for side in ["challenger", "opponent"]:
            stats = battle_data.get(f"{side}_stats")
            if not stats:
                continue

            # Process status effects
            for status in stats.get("status_effects", []).copy():
                # DOT damage
                if "dot_damage" in status:
                    damage = status["dot_damage"]
                    stats["current_hp"] -= damage
                    messages.append(
                        f"{stats['name']} took {damage} damage from {status['name']}!"
                    )

                # Status duration
                status["turns"] -= 1
                if status["turns"] <= 0:
                    stats["status_effects"].remove(status)
                    messages.append(f"{stats['name']} recovered from {status['name']}!")

            # Resource regeneration
            for resource in ["energy", "mana", "rage"]:
                if f"current_{resource}" in stats:
                    regen = stats.get(f"{resource}_regen", 0)
                    if regen:
                        current = stats[f"current_{resource}"]
                        max_val = stats[f"max_{resource}"]
                        stats[f"current_{resource}"] = min(max_val, current + regen)

            battle_data[f"{side}_stats"] = stats

        return battle_data, "\n".join(messages)

    def apply_status_effects(
        self, stats: Dict[str, Any], status_effects: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], str]:
        """Apply status effects and return modified stats + message."""
        message = ""
        modified_stats = stats.copy()

        for effect, data in status_effects.items():
            if data["turns"] > 0:
                if effect == "burn":
                    damage = max(1, int(stats["max_hp"] * 0.0625))
                    modified_stats["hp"] -= damage
                    message += f"\nBurn dealt {damage} damage!"
                elif effect == "poison":
                    damage = max(1, int(stats["max_hp"] * 0.125))
                    modified_stats["hp"] -= damage
                    message += f"\nPoison dealt {damage} damage!"
                elif effect == "paralyze":
                    if random.random() < 0.25:
                        modified_stats["can_move"] = False
                        message += "\nParalysis prevented movement!"
                data["turns"] -= 1
            else:
                del status_effects[effect]
                message += f"\nRecovered from {effect}!"

        return modified_stats, message

    def check_battle_end(self, battle_state: BattleState) -> Tuple[bool, Optional[int]]:
        """Check if battle should end and return winner if any."""
        if not battle_state or battle_state.is_finished:
            return True, battle_state.winner_id if battle_state else None

        challenger_stats = battle_state.battle_data.get("challenger_stats", {})
        opponent_stats = battle_state.battle_data.get("opponent_stats", {})

        if challenger_stats.get("hp", 0) <= 0:
            return True, battle_state.opponent_id
        elif opponent_stats.get("hp", 0) <= 0:
            return True, battle_state.challenger_id

        return False, None
