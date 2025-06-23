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
            "accurate": {
                "attack_bonus": 3,
                "accuracy_multiplier": 1.1,
                "xp_type": "attack",
            },
            "aggressive": {
                "strength_bonus": 3,
                "damage_multiplier": 1.1,
                "xp_type": "strength",
            },
            "defensive": {
                "defence_bonus": 3,
                "defence_multiplier": 1.1,
                "xp_type": "defence",
            },
            "controlled": {
                "all_bonus": 1,
                "accuracy_multiplier": 1.05,
                "xp_type": "shared",
            },
            "rapid": {
                "attack_speed_bonus": 1,
                "accuracy_multiplier": 0.9,
                "xp_type": "ranged",
            },
            "longrange": {"defence_bonus": 2, "range_bonus": 2, "xp_type": "shared"},
        }

        self.prayer_boosts = {
            "piety": {
                "attack": 1.20,
                "strength": 1.23,
                "defence": 1.25,
                "prayer_drain": 4,
            },
            "rigour": {
                "ranged": 1.23,
                "ranged_str": 1.23,
                "defence": 1.25,
                "prayer_drain": 4,
            },
            "augury": {
                "magic": 1.25,
                "magic_def": 1.25,
                "defence": 1.25,
                "prayer_drain": 4,
            },
            "protect_melee": {"damage_reduction": 0.4, "prayer_drain": 1},
            "protect_ranged": {"damage_reduction": 0.4, "prayer_drain": 1},
            "protect_magic": {"damage_reduction": 0.4, "prayer_drain": 1},
        }

    def calculate_damage(
        self, move: str, attacker_stats: Dict[str, Any], defender_stats: Dict[str, Any]
    ) -> Tuple[int, str]:
        """Calculate damage using OSRS combat formulas."""
        # Get base stats
        attack_level = attacker_stats["skills"]["attack"]
        strength_level = attacker_stats["skills"]["strength"]
        equipment_bonus = attacker_stats.get("equipment_bonus", 0)

        # Get style bonuses
        style = attacker_stats.get("combat_style", "controlled")
        style_mods = self.combat_styles[style]

        # Apply prayer effects
        prayer_bonus = 1.0
        if active_prayers := attacker_stats.get("active_prayers", []):
            for prayer in active_prayers:
                if boosts := self.prayer_boosts.get(prayer):
                    if "strength" in boosts:
                        prayer_bonus *= boosts["strength"]

        # Calculate max hit
        max_hit = calculate_max_hit(
            strength_level=strength_level,
            equipment_bonus=equipment_bonus,
            prayer_bonus=prayer_bonus,
            other_bonus=style_mods.get("damage_multiplier", 1.0),
        )

        # Roll for damage
        damage = random.randint(0, max_hit)

        # Check accuracy
        accuracy = self._calculate_accuracy(
            attack_level=attack_level + style_mods.get("attack_bonus", 0),
            equipment_bonus=equipment_bonus,
            target_defence=defender_stats["skills"]["defence"],
            style_multiplier=style_mods.get("accuracy_multiplier", 1.0),
        )

        # Apply protection prayers
        if defender_prayers := defender_stats.get("active_prayers", []):
            for prayer in defender_prayers:
                if "protect" in prayer and prayer.split("_")[1] in move:
                    damage = int(damage * 0.6)  # Protection prayers reduce damage by 40%
                    break

        # Check if hit lands
        if random.random() > accuracy:
            return 0, "The attack missed!"

        message = []
        message.append(f"Hit for {damage} damage!")
        if damage == max_hit:
            message.append("Maximum hit!")
        if damage == 0:
            message.append("Failed to penetrate defense!")

        return damage, " ".join(message)

    def process_turn(self, battle_state: BattleState, move: str) -> Dict[str, Any]:
        """Process a combat turn."""
        battle_data = battle_state.battle_data
        attacker_id = battle_state.current_turn

        # Get attacker and defender stats
        attacker_stats = battle_data[
            ("challenger_stats" if attacker_id == battle_state.challenger_id else "opponent_stats")
        ]
        defender_stats = battle_data[
            ("opponent_stats" if attacker_id == battle_state.challenger_id else "challenger_stats")
        ]

        # Apply combat effects
        attacker_stats = self._apply_combat_effects(attacker_stats)
        defender_stats = self._apply_combat_effects(defender_stats)

        # Calculate and apply damage
        damage, message = self.calculate_damage(move, attacker_stats, defender_stats)

        # Update hitpoints
        defender_stats["hitpoints"] -= damage

        # Check if defender died
        battle_end_message = ""
        if defender_stats["hitpoints"] <= 0:
            battle_state.is_finished = True
            battle_state.winner_id = attacker_id
            battle_end_message = "\nKnockout! The battle is over!"

        return {
            "damage": damage,
            "message": message + battle_end_message,
            "attacker_id": attacker_id,
            "defender_hp": defender_stats["hitpoints"],
            "xp_gained": self._calculate_xp_gain(damage, self.combat_styles[move]["xp_type"]),
        }

    def _calculate_xp_gain(self, damage: int, xp_type: str) -> Dict[str, float]:
        """Calculate experience gained from an attack."""
        base_xp = damage * 4  # OSRS gives 4 xp per damage dealt

        if xp_type == "shared":
            return {
                "attack": base_xp / 3,
                "strength": base_xp / 3,
                "defence": base_xp / 3,
            }
        else:
            return {xp_type: base_xp}

    def is_valid_move(self, battle_state: BattleState, move: str, player_id: int) -> bool:
        """Validate combat move."""
        if not battle_state or battle_state.is_finished:
            return False

        if battle_state.current_turn != player_id:
            return False

        return move in self.get_available_moves(battle_state, player_id)

    def get_available_moves(self, battle_state: BattleState, player_id: int) -> list[str]:
        """Get available combat moves."""
        if not battle_state or battle_state.is_finished:
            return []

        stats = battle_state.battle_data.get(
            "challenger_stats" if player_id == battle_state.challenger_id else "opponent_stats"
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
