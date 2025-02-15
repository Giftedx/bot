"""Abstract base battle system for all battle types."""

import random
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from .battle_manager import BattleState, BattleType


class BaseBattleSystem(ABC):
    """Abstract base class for battle systems."""

    def __init__(self, battle_type: BattleType):
        self.battle_type = battle_type

    @abstractmethod
    def calculate_damage(
        self, move: str, attacker_stats: Dict[str, Any], defender_stats: Dict[str, Any]
    ) -> Tuple[int, str]:
        """Calculate damage and return amount + effect message."""
        pass

    @abstractmethod
    def process_turn(self, battle_state: BattleState, move: str) -> Dict[str, Any]:
        """Process a turn and return the turn results."""
        pass

    @abstractmethod
    def is_valid_move(
        self, battle_state: BattleState, move: str, player_id: int
    ) -> bool:
        """Validate if a move is legal for the current state."""
        pass

    @abstractmethod
    def get_available_moves(
        self, battle_state: BattleState, player_id: int
    ) -> list[str]:
        """Get list of available moves for a player."""
        pass

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
