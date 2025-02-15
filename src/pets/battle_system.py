"""Pet battle system implementation."""

import random
from typing import Any, Dict, Optional, Tuple

from src.core.battle_manager import BattleState, BattleType
from src.core.battle_system import BaseBattleSystem


class PetBattleSystem(BaseBattleSystem):
    """Pet battle system with elemental interactions."""

    def __init__(self):
        super().__init__(BattleType.PET)
        self.element_chart = {
            "fire": {"earth": 2.0, "ice": 2.0, "nature": 0.5, "water": 0.5},
            "water": {"fire": 2.0, "earth": 0.5, "lightning": 0.5},
            "earth": {"lightning": 2.0, "water": 2.0, "fire": 0.5},
            "air": {"earth": 2.0, "lightning": 0.5},
            "lightning": {"water": 2.0, "air": 2.0, "earth": 0.5},
            "light": {"dark": 2.0, "shadow": 0.5},
            "dark": {"light": 2.0, "psychic": 2.0},
            "nature": {"water": 2.0, "fire": 0.5},
            "ice": {"nature": 2.0, "fire": 0.5},
            "psychic": {"dark": 0.5},
            "shadow": {"light": 2.0},
        }

        self.status_effects = {
            "burn": {"dot": 5, "turns": 3},
            "poison": {"dot": 8, "turns": 3},
            "stun": {"skip_turn": True, "turns": 1},
            "weakness": {"stat_mod": {"attack": 0.75}, "turns": 2},
            "vulnerable": {"stat_mod": {"defense": 0.75}, "turns": 2},
        }

    def calculate_damage(
        self, move: str, attacker_stats: Dict[str, Any], defender_stats: Dict[str, Any]
    ) -> Tuple[int, str]:
        """Calculate pet move damage using elements and stats."""
        move_data = attacker_stats["moves"][move]

        # Base damage calculation
        base_damage = move_data["power"]
        attack = attacker_stats["stats"]["attack"]
        defense = defender_stats["stats"]["defense"]

        # Level scaling
        level_mod = attacker_stats["level"] / 100

        # Element effectiveness
        effectiveness = self._calculate_element_bonus(
            move_data["element"], defender_stats["element"]
        )

        # Loyalty bonus (unique to pets)
        loyalty_mod = min(1.5, 1 + (attacker_stats["loyalty"] / 200))

        # Calculate final damage
        damage = (
            (base_damage * attack / defense) * level_mod * effectiveness * loyalty_mod
        )
        damage = max(1, int(damage))

        # Build effect message
        message = []
        if effectiveness > 1:
            message.append(f"{move} was super effective!")
        elif effectiveness < 1:
            message.append(f"{move} was not very effective...")

        if loyalty_mod > 1.2:
            message.append("Your pet's loyalty strengthened the attack!")

        return damage, " ".join(message)

    def process_turn(self, battle_state: BattleState, move: str) -> Dict[str, Any]:
        """Process a pet battle turn."""
        battle_data = battle_state.battle_data
        attacker_id = battle_state.current_turn

        # Get attacker and defender stats
        if attacker_id == battle_state.challenger_id:
            attacker = battle_data["challenger_pet"]
            defender = battle_data["opponent_pet"]
        else:
            attacker = battle_data["opponent_pet"]
            defender = battle_data["challenger_pet"]

        # Get move data
        move_data = attacker["moves"][move]

        # Check energy cost
        if attacker["current_energy"] < move_data["energy_cost"]:
            return {"success": False, "message": f"Not enough energy to use {move}!"}

        # Apply energy cost
        attacker["current_energy"] -= move_data["energy_cost"]

        # Calculate damage
        damage, effect_message = self.calculate_damage(move, attacker, defender)

        # Apply damage
        defender["current_hp"] -= damage

        # Apply status effects
        status_message = ""
        if "status_effect" in move_data:
            effect = move_data["status_effect"]
            if random.random() < move_data["status_chance"]:
                if effect not in defender["status_effects"]:
                    defender["status_effects"][effect] = self.status_effects[
                        effect
                    ].copy()
                    status_message = (
                        f"\n{defender['name']} was afflicted with {effect}!"
                    )

        # Regenerate some energy
        attacker["current_energy"] = min(
            attacker["max_energy"],
            attacker["current_energy"] + attacker["energy_regen"],
        )

        return {
            "damage": damage,
            "message": (
                f"{attacker['name']} used {move}!\n" f"{effect_message}{status_message}"
            ),
            "attacker_id": attacker_id,
            "defender_hp": defender["current_hp"],
            "attacker_energy": attacker["current_energy"],
        }

    def is_valid_move(
        self, battle_state: BattleState, move: str, player_id: int
    ) -> bool:
        """Validate pet move."""
        if not battle_state or battle_state.is_finished:
            return False

        if battle_state.current_turn != player_id:
            return False

        # Get pet data
        pet = battle_state.battle_data.get(
            "challenger_pet"
            if player_id == battle_state.challenger_id
            else "opponent_pet"
        )

        # Check move exists and energy cost
        if not pet or move not in pet.get("moves", {}):
            return False

        return pet["current_energy"] >= pet["moves"][move]["energy_cost"]

    def get_available_moves(
        self, battle_state: BattleState, player_id: int
    ) -> list[str]:
        """Get available pet moves."""
        if not battle_state or battle_state.is_finished:
            return []

        pet = battle_state.battle_data.get(
            "challenger_pet"
            if player_id == battle_state.challenger_id
            else "opponent_pet"
        )

        if not pet:
            return []

        # Return moves with sufficient energy
        return [
            move
            for move, data in pet.get("moves", {}).items()
            if pet["current_energy"] >= data["energy_cost"]
        ]

    def _calculate_element_bonus(
        self, attack_element: str, defend_element: str
    ) -> float:
        """Calculate elemental effectiveness modifier."""
        if multiplier := self.element_chart.get(attack_element, {}).get(defend_element):
            return multiplier
        return 1.0
