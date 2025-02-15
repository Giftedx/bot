"""OSRS combat system implementation."""

import random
from math import floor
from typing import Any, Dict, Optional, Tuple

from src.core.battle_manager import BattleState, BattleType
from src.core.battle_system import BaseBattleSystem
from src.osrs.core.game_math import calculate_max_hit


class OSRSBattleSystem(BaseBattleSystem):
    """OSRS combat system using official formulas."""

    def __init__(self):
        super().__init__(BattleType.OSRS)
        self.combat_styles = {
            "accurate": {"attack_bonus": 3, "accuracy_multiplier": 1.1},
            "aggressive": {"strength_bonus": 3, "damage_multiplier": 1.1},
            "defensive": {"defence_bonus": 3, "defence_multiplier": 1.1},
            "controlled": {"all_bonus": 1, "accuracy_multiplier": 1.05},
            "rapid": {"attack_speed_bonus": 1, "accuracy_multiplier": 0.9},
            "longrange": {"defence_bonus": 2, "range_bonus": 2},
        }

    def calculate_damage(
        self, move: str, attacker_stats: Dict[str, Any], defender_stats: Dict[str, Any]
    ) -> Tuple[int, str]:
        """Calculate damage using OSRS combat formulas."""
        # Get base stats
        attack_level = attacker_stats["skills"]["attack"]
        strength_level = attacker_stats["skills"]["strength"]
        equipment_bonus = attacker_stats.get("equipment_bonus", 0)
        prayer_bonus = attacker_stats.get("prayer_bonus", 1.0)

        # Apply combat style bonuses
        style = attacker_stats.get("combat_style", "controlled")
        style_mods = self.combat_styles[style]

        # Calculate max hit using OSRS formula
        max_hit = calculate_max_hit(
            strength_level=strength_level,
            equipment_bonus=equipment_bonus,
            prayer_bonus=prayer_bonus,
            other_bonus=style_mods.get("damage_multiplier", 1.0),
        )

        # Roll for hit
        damage = random.randint(0, max_hit)

        # Calculate accuracy
        accuracy = self._calculate_accuracy(
            attack_level=attack_level,
            equipment_bonus=equipment_bonus,
            target_defence=defender_stats["skills"]["defence"],
            style_multiplier=style_mods.get("accuracy_multiplier", 1.0),
        )

        # Check if hit lands
        if random.random() > accuracy:
            return 0, "The attack missed!"

        message = f"Hit for {damage} damage!"
        if damage == max_hit:
            message += " Maximum hit!"

        return damage, message

    def process_turn(self, battle_state: BattleState, move: str) -> Dict[str, Any]:
        """Process a combat turn."""
        battle_data = battle_state.battle_data
        attacker_id = battle_state.current_turn

        # Get attacker and defender stats
        if attacker_id == battle_state.challenger_id:
            attacker_stats = battle_data["challenger_stats"]
            defender_stats = battle_data["opponent_stats"]
        else:
            attacker_stats = battle_data["opponent_stats"]
            defender_stats = battle_data["challenger_stats"]

        # Apply any active prayers/effects
        attacker_stats = self._apply_combat_effects(attacker_stats)

        # Calculate and apply damage
        damage, message = self.calculate_damage(move, attacker_stats, defender_stats)

        defender_stats["hitpoints"] -= damage

        return {
            "damage": damage,
            "message": message,
            "attacker_id": attacker_id,
            "defender_hp": defender_stats["hitpoints"],
        }

    def is_valid_move(
        self, battle_state: BattleState, move: str, player_id: int
    ) -> bool:
        """Validate combat move."""
        if not battle_state or battle_state.is_finished:
            return False

        if battle_state.current_turn != player_id:
            return False

        return move in self.get_available_moves(battle_state, player_id)

    def get_available_moves(
        self, battle_state: BattleState, player_id: int
    ) -> list[str]:
        """Get available combat moves."""
        if not battle_state or battle_state.is_finished:
            return []

        stats = battle_state.battle_data.get(
            "challenger_stats"
            if player_id == battle_state.challenger_id
            else "opponent_stats"
        )

        if not stats:
            return []

        # Get weapon type moves
        weapon_type = stats.get("equipment", {}).get("weapon_type", "unarmed")
        return self._get_weapon_moves(weapon_type)

    def _calculate_accuracy(
        self,
        attack_level: int,
        equipment_bonus: int,
        target_defence: int,
        style_multiplier: float = 1.0,
    ) -> float:
        """Calculate hit chance using OSRS accuracy formula."""
        effective_level = floor(attack_level * style_multiplier)
        attack_roll = effective_level * (equipment_bonus + 64)
        defence_roll = target_defence * 64

        if attack_roll > defence_roll:
            return 1 - (defence_roll + 2) / (2 * (attack_roll + 1))
        else:
            return attack_roll / (2 * defence_roll + 2)

    def _apply_combat_effects(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Apply active combat boosts and effects."""
        modified = stats.copy()

        # Apply prayer boosts
        if active_prayers := stats.get("active_prayers", []):
            for prayer in active_prayers:
                if prayer == "piety":
                    modified["skills"]["attack"] *= 1.20
                    modified["skills"]["strength"] *= 1.23
                    modified["skills"]["defence"] *= 1.25
                elif prayer == "rigour":
                    modified["skills"]["ranged"] *= 1.23
                    modified["skills"]["defence"] *= 1.25
                elif prayer == "augury":
                    modified["skills"]["magic"] *= 1.25
                    modified["skills"]["defence"] *= 1.25

        return modified

    def _get_weapon_moves(self, weapon_type: str) -> list[str]:
        """Get available moves for weapon type."""
        base_moves = list(self.combat_styles.keys())

        if weapon_type == "unarmed":
            return ["accurate", "aggressive", "defensive"]
        elif weapon_type in ["sword", "scimitar"]:
            return ["accurate", "aggressive", "defensive", "controlled"]
        elif weapon_type in ["bow", "crossbow"]:
            return ["accurate", "rapid", "longrange"]
        elif weapon_type == "staff":
            return ["accurate", "aggressive", "defensive", "autocast"]

        return base_moves
