"""Pokemon battle system implementation."""

import random
from typing import Any, Dict, Tuple

from src.core.battle_manager import BattleState, BattleType
from src.core.battle_system import BaseBattleSystem


class PokemonBattleSystem(BaseBattleSystem):
    """Pokemon battle system using type effectiveness and stats."""

    def __init__(self):
        super().__init__(BattleType.POKEMON)
        # Complete type chart using official Pokemon type effectiveness
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

        self.status_effects = {
            "burn": {
                "damage": lambda max_hp: max_hp // 16,
                "stat_mod": {"attack": 0.5},
                "cure_chance": 0.15,
            },
            "poison": {
                "damage": lambda max_hp: max_hp // 8,
                "stat_mod": {},
                "cure_chance": 0.15,
            },
            "toxic": {
                "damage": lambda max_hp, turns: (max_hp // 16) * min(turns, 15),
                "stat_mod": {},
                "cure_chance": 0.15,
            },
            "paralyze": {
                "skip_chance": 0.25,
                "stat_mod": {"speed": 0.5},
                "cure_chance": 0.15,
            },
            "sleep": {
                "wake_chance": 0.34,
                "stat_mod": {},
                "turns": lambda: random.randint(1, 3),
            },
            "freeze": {"thaw_chance": 0.2, "stat_mod": {}, "break_on_fire": True},
        }

    def calculate_damage(
        self, move: str, attacker_stats: Dict[str, Any], defender_stats: Dict[str, Any]
    ) -> Tuple[int, str]:
        """Calculate Pokemon move damage using type effectiveness."""
        move_data = attacker_stats["moves"][move]

        # Skip damage calc for status moves
        if move_data["category"] == "status":
            return 0, self._apply_status_effect(move_data, defender_stats)

        # Base power calculation
        power = move_data["power"]

        # STAB (Same Type Attack Bonus)
        stab = 1.5 if move_data["type"] in attacker_stats["types"] else 1.0

        # Type effectiveness
        effectiveness = self._calculate_effectiveness(move_data["type"], defender_stats["types"])

        # Critical hit (6.25% chance)
        is_crit = random.random() < 0.0625
        crit_mod = 1.5 if is_crit else 1.0

        # Stat stages and status effects
        attack_stat = "special_attack" if move_data["category"] == "special" else "attack"
        defense_stat = "special_defense" if move_data["category"] == "special" else "defense"

        attack = self._apply_stat_stages(
            attacker_stats["stats"][attack_stat],
            attacker_stats.get("stat_stages", {}).get(attack_stat, 0),
        )

        defense = self._apply_stat_stages(
            defender_stats["stats"][defense_stat],
            defender_stats.get("stat_stages", {}).get(defense_stat, 0),
        )

        # Status effects
        if attacker_stats.get("status") == "burn" and move_data["category"] == "physical":
            attack *= 0.5

        # Final damage formula
        level = attacker_stats["level"]
        damage = ((2 * level / 5 + 2) * power * attack / defense) / 50 + 2
        damage *= stab * effectiveness * crit_mod

        # Random factor (85-100%)
        damage *= random.randint(85, 100) / 100

        damage = max(1, int(damage))

        # Build message
        messages = []
        if effectiveness > 1:
            messages.append("It's super effective!")
        elif effectiveness < 1 and effectiveness > 0:
            messages.append("It's not very effective...")
        elif effectiveness == 0:
            messages.append("It had no effect...")
        if is_crit:
            messages.append("A critical hit!")

        return damage, " ".join(messages)

    def process_turn(self, battle_state: BattleState, move: str) -> Dict[str, Any]:
        """Process a Pokemon battle turn."""
        battle_data = battle_state.battle_data
        attacker_id = battle_state.current_turn

        # Get attacker and defender stats
        attacker_stats = battle_data[
            (
                "challenger_pokemon"
                if attacker_id == battle_state.challenger_id
                else "opponent_pokemon"
            )
        ]
        defender_stats = battle_data[
            (
                "opponent_pokemon"
                if attacker_id == battle_state.challenger_id
                else "challenger_pokemon"
            )
        ]

        # Check for status preventing move
        if status := attacker_stats.get("status"):
            if status == "freeze":
                if not self._can_move_while_frozen(attacker_stats, move):
                    return {
                        "success": False,
                        "message": f"{attacker_stats['name']} is frozen solid!",
                    }
            elif status == "sleep":
                if not self._try_wake_up(attacker_stats):
                    return {
                        "success": False,
                        "message": f"{attacker_stats['name']} is fast asleep!",
                    }
            elif status == "paralyze":
                if random.random() < 0.25:
                    return {
                        "success": False,
                        "message": f"{attacker_stats['name']} is paralyzed! It can't move!",
                    }

        # Get move data and check PP
        move_data = attacker_stats["moves"][move]
        if move_data["pp"] <= 0:
            return {"success": False, "message": f"{move} has no PP left!"}

        # Use PP
        move_data["pp"] -= 1

        # Calculate damage
        damage, effect_message = self.calculate_damage(move, attacker_stats, defender_stats)

        # Apply damage
        defender_stats["current_hp"] -= damage

        # Apply move effects
        status_message = ""
        if effect := move_data.get("effect"):
            status_message = self._apply_move_effect(effect, attacker_stats, defender_stats)

        # Apply end of turn effects
        end_turn_message = self._apply_end_turn_effects(attacker_stats, defender_stats)

        return {
            "damage": damage,
            "message": (
                f"{attacker_stats['name']} used {move}!\n"
                f"{effect_message}\n{status_message}\n{end_turn_message}"
            ).strip(),
            "attacker_id": attacker_id,
            "defender_hp": defender_stats["current_hp"],
        }

    def _calculate_effectiveness(self, move_type: str, defender_types: list[str]) -> float:
        """Calculate type effectiveness modifier."""
        effectiveness = 1.0
        for def_type in defender_types:
            if multiplier := self.type_chart.get(move_type, {}).get(def_type):
                effectiveness *= multiplier
        return effectiveness

    def _apply_stat_stages(self, base_stat: int, stage: int) -> int:
        """Apply stat stage multipliers."""
        if stage > 0:
            return int(base_stat * (2 + stage) / 2)
        elif stage < 0:
            return int(base_stat * 2 / (2 - stage))
        return base_stat

    def _can_move_while_frozen(self, pokemon: Dict[str, Any], move: str) -> bool:
        """Check if frozen Pokemon can move."""
        move_data = pokemon["moves"][move]
        if move_data["type"] == "fire":  # Fire moves thaw the user
            pokemon["status"] = None
            return True
        return random.random() < 0.2  # 20% chance to thaw

    def _try_wake_up(self, pokemon: Dict[str, Any]) -> bool:
        """Try to wake up from sleep."""
        if random.random() < 0.34:  # 34% chance to wake up
            pokemon["status"] = None
            return True
        return False

    def _apply_end_turn_effects(self, attacker: Dict[str, Any], defender: Dict[str, Any]) -> str:
        """Apply end of turn status effects."""
        messages = []

        for pokemon in [attacker, defender]:
            if status := pokemon.get("status"):
                effect = self.status_effects[status]

                if "damage" in effect:
                    if status == "toxic":
                        turns = pokemon.get("toxic_turns", 1)
                        damage = effect["damage"](pokemon["stats"]["hp"], turns)
                        pokemon["toxic_turns"] = turns + 1
                    else:
                        damage = effect["damage"](pokemon["stats"]["hp"])

                    pokemon["current_hp"] -= damage
                    messages.append(f"{pokemon['name']} was hurt by {status}!")

        return "\n".join(messages)

    def is_valid_move(self, battle_state: BattleState, move: str, player_id: int) -> bool:
        """Validate if a move can be used."""
        if not battle_state or battle_state.is_finished:
            return False

        if battle_state.current_turn != player_id:
            return False

        pokemon = battle_state.battle_data.get(
            "challenger_pokemon" if player_id == battle_state.challenger_id else "opponent_pokemon"
        )

        return move in pokemon.get("moves", {}) and pokemon["moves"][move]["pp"] > 0

    def get_available_moves(self, battle_state: BattleState, player_id: int) -> list[str]:
        """Get list of moves that can be used."""
        if not battle_state or battle_state.is_finished:
            return []

        pokemon = battle_state.battle_data.get(
            "challenger_pokemon" if player_id == battle_state.challenger_id else "opponent_pokemon"
        )

        if not pokemon:
            return []

        return [move for move, data in pokemon.get("moves", {}).items() if data["pp"] > 0]
