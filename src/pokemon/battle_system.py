"""Pokemon battle system implementation."""

import random
from typing import Any, Dict, Optional, Tuple

from src.core.battle_manager import BattleState, BattleType
from src.core.battle_system import BaseBattleSystem


class PokemonBattleSystem(BaseBattleSystem):
    """Pokemon battle system using type effectiveness and stats."""

    def __init__(self):
        super().__init__(BattleType.POKEMON)
        self.type_chart = {
            "normal": {"rock": 0.5, "ghost": 0, "steel": 0.5},
            "fire": {
                "fire": 0.5,
                "water": 0.5,
                "grass": 2,
                "ice": 2,
                "bug": 2,
                "rock": 0.5,
                "dragon": 0.5,
                "steel": 2,
            },
            "water": {
                "fire": 2,
                "water": 0.5,
                "grass": 0.5,
                "ground": 2,
                "rock": 2,
                "dragon": 0.5,
            },
            "electric": {
                "water": 2,
                "electric": 0.5,
                "grass": 0.5,
                "ground": 0,
                "flying": 2,
                "dragon": 0.5,
            },
            "grass": {
                "fire": 0.5,
                "water": 2,
                "grass": 0.5,
                "poison": 0.5,
                "ground": 2,
                "flying": 0.5,
                "bug": 0.5,
                "rock": 2,
                "dragon": 0.5,
                "steel": 0.5,
            },
            "ice": {
                "fire": 0.5,
                "water": 0.5,
                "grass": 2,
                "ice": 0.5,
                "ground": 2,
                "flying": 2,
                "dragon": 2,
                "steel": 0.5,
            },
            "fighting": {
                "normal": 2,
                "ice": 2,
                "poison": 0.5,
                "flying": 0.5,
                "psychic": 0.5,
                "bug": 0.5,
                "rock": 2,
                "ghost": 0,
                "dark": 2,
                "steel": 2,
            },
            "poison": {
                "grass": 2,
                "poison": 0.5,
                "ground": 0.5,
                "rock": 0.5,
                "ghost": 0.5,
                "steel": 0,
            },
            "ground": {
                "fire": 2,
                "electric": 2,
                "grass": 0.5,
                "poison": 2,
                "flying": 0,
                "bug": 0.5,
                "rock": 2,
                "steel": 2,
            },
            "flying": {
                "electric": 0.5,
                "grass": 2,
                "fighting": 2,
                "bug": 2,
                "rock": 0.5,
                "steel": 0.5,
            },
            "psychic": {
                "fighting": 2,
                "poison": 2,
                "psychic": 0.5,
                "dark": 0,
                "steel": 0.5,
            },
            "bug": {
                "fire": 0.5,
                "grass": 2,
                "fighting": 0.5,
                "poison": 0.5,
                "flying": 0.5,
                "psychic": 2,
                "ghost": 0.5,
                "dark": 2,
                "steel": 0.5,
            },
            "rock": {
                "fire": 2,
                "ice": 2,
                "fighting": 0.5,
                "ground": 0.5,
                "flying": 2,
                "bug": 2,
                "steel": 0.5,
            },
            "ghost": {"normal": 0, "psychic": 2, "ghost": 2, "dark": 0.5},
            "dragon": {"dragon": 2, "steel": 0.5},
            "dark": {"fighting": 0.5, "psychic": 2, "ghost": 2, "dark": 0.5},
            "steel": {
                "fire": 0.5,
                "water": 0.5,
                "electric": 0.5,
                "ice": 2,
                "rock": 2,
                "steel": 0.5,
            },
        }

    def calculate_damage(
        self, move: str, attacker_stats: Dict[str, Any], defender_stats: Dict[str, Any]
    ) -> Tuple[int, str]:
        """Calculate Pokemon move damage using type effectiveness."""
        move_data = attacker_stats["moves"][move]

        # Base power calculation
        power = move_data["power"]

        # STAB (Same Type Attack Bonus)
        stab = 1.5 if move_data["type"] in attacker_stats["types"] else 1.0

        # Type effectiveness
        effectiveness = self._calculate_effectiveness(
            move_data["type"], defender_stats["types"]
        )

        # Critical hit (6.25% chance)
        is_crit = random.random() < 0.0625
        crit_mod = 1.5 if is_crit else 1.0

        # Final damage formula (simplified from actual games)
        level = attacker_stats["level"]
        attack = attacker_stats["stats"]["attack"]
        defense = defender_stats["stats"]["defense"]

        damage = ((2 * level / 5 + 2) * power * attack / defense) / 50 + 2
        damage *= stab * effectiveness * crit_mod
        damage = max(1, int(damage))

        # Build message
        message = []
        if is_crit:
            message.append("A critical hit!")
        if effectiveness > 1:
            message.append("It's super effective!")
        elif effectiveness < 1:
            message.append("It's not very effective...")
        elif effectiveness == 0:
            message.append("It had no effect...")

        return damage, " ".join(message)

    def process_turn(self, battle_state: BattleState, move: str) -> Dict[str, Any]:
        """Process a Pokemon battle turn."""
        battle_data = battle_state.battle_data
        attacker_id = battle_state.current_turn

        # Get attacker and defender stats
        if attacker_id == battle_state.challenger_id:
            attacker_stats = battle_data["challenger_pokemon"]
            defender_stats = battle_data["opponent_pokemon"]
        else:
            attacker_stats = battle_data["opponent_pokemon"]
            defender_stats = battle_data["challenger_pokemon"]

        # Get move data
        move_data = attacker_stats["moves"][move]

        # Check PP
        if move_data["pp"] <= 0:
            return {"success": False, "message": f"{move} has no PP left!"}

        # Reduce PP
        move_data["pp"] -= 1

        # Calculate and apply damage
        damage, effect_message = self.calculate_damage(
            move, attacker_stats, defender_stats
        )

        defender_stats["current_hp"] -= damage

        # Apply status effects if any
        status_message = ""
        if status_effect := move_data.get("status_effect"):
            if random.random() < move_data["status_chance"]:
                defender_stats["status"] = status_effect
                status_message = f"\n{defender_stats['name']} was {status_effect}!"

        return {
            "damage": damage,
            "message": (
                f"{attacker_stats['name']} used {move}!\n"
                f"{effect_message}{status_message}"
            ),
            "attacker_id": attacker_id,
            "defender_hp": defender_stats["current_hp"],
        }

    def is_valid_move(
        self, battle_state: BattleState, move: str, player_id: int
    ) -> bool:
        """Validate Pokemon move."""
        if not battle_state or battle_state.is_finished:
            return False

        if battle_state.current_turn != player_id:
            return False

        # Get pokemon moves
        pokemon = battle_state.battle_data.get(
            "challenger_pokemon"
            if player_id == battle_state.challenger_id
            else "opponent_pokemon"
        )

        return move in pokemon.get("moves", {})

    def get_available_moves(
        self, battle_state: BattleState, player_id: int
    ) -> list[str]:
        """Get available Pokemon moves."""
        if not battle_state or battle_state.is_finished:
            return []

        pokemon = battle_state.battle_data.get(
            "challenger_pokemon"
            if player_id == battle_state.challenger_id
            else "opponent_pokemon"
        )

        if not pokemon:
            return []

        # Only return moves with PP remaining
        return [
            move for move, data in pokemon.get("moves", {}).items() if data["pp"] > 0
        ]

    def _calculate_effectiveness(
        self, move_type: str, defender_types: list[str]
    ) -> float:
        """Calculate type effectiveness modifier."""
        effectiveness = 1.0

        for def_type in defender_types:
            if multiplier := self.type_chart.get(move_type, {}).get(def_type):
                effectiveness *= multiplier

        return effectiveness
