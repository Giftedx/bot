"""Base battle system interface and shared functionality."""

import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, TypeVar
from enum import Enum
from datetime import datetime

from src.core.battle_manager import BattleState, BattleType
from .pet_system import Pet, PetOrigin, PetAbility
from ..features.pets.event_system import EventManager, EventType, GameEvent

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


class BattleResult:
    def __init__(self, winner: Pet, loser: Pet, battle_type: BattleType,
                 rounds: int, exp_gained: int, ability_logs: List[Dict[str, Any]]):
        self.winner = winner
        self.loser = loser
        self.battle_type = battle_type
        self.rounds = rounds
        self.exp_gained = exp_gained
        self.ability_logs = ability_logs
        self.timestamp = datetime.utcnow()


class Battle:
    def __init__(self, pet1: Pet, pet2: Pet, battle_type: BattleType,
                 event_manager: Optional[EventManager] = None):
        self.pet1 = pet1
        self.pet2 = pet2
        self.battle_type = battle_type
        self.state = BattleState.WAITING
        self.current_round = 0
        self.max_rounds = 10
        self.event_manager = event_manager
        self.ability_logs: List[Dict[str, Any]] = []
        self.last_ability_used: Dict[str, datetime] = {}

    def _calculate_damage(self, attacker: Pet, defender: Pet, ability: Optional[PetAbility] = None) -> int:
        """Calculate damage for an attack"""
        # Base damage from attack stat
        base_damage = attacker.stats.skill_levels["attack"] * 5

        # Apply level scaling
        level_scaling = attacker.stats.level / defender.stats.level
        base_damage *= min(max(level_scaling, 0.5), 2.0)  # Cap scaling between 0.5x and 2x

        # Apply type advantages for cross-system battles
        type_multiplier = 1.0
        if self.battle_type == BattleType.CROSS_SYSTEM:
            if attacker.origin == PetOrigin.OSRS and defender.origin == PetOrigin.POKEMON:
                # OSRS pets deal more damage to Pokemon
                type_multiplier = 1.2
            elif attacker.origin == PetOrigin.POKEMON and defender.origin == PetOrigin.OSRS:
                # Pokemon deal less damage to OSRS pets
                type_multiplier = 0.8

        # Apply ability effects
        ability_multiplier = 1.0
        if ability:
            if ability.effect_type == "damage":
                ability_multiplier += ability.effect_value
            elif ability.effect_type == "defense_break":
                defender.stats.skill_levels["defense"] *= (1 - ability.effect_value)

        # Apply defense reduction
        defense_reduction = defender.stats.skill_levels["defense"] / 100  # 1% reduction per defense level
        final_damage = int(base_damage * (1 - defense_reduction) * type_multiplier * ability_multiplier)
        
        # Add randomness
        return max(1, final_damage + random.randint(-5, 5))

    def _can_use_ability(self, pet: Pet, ability: PetAbility) -> bool:
        """Check if an ability can be used"""
        ability_key = f"{pet.pet_id}_{ability.name}"
        last_used = self.last_ability_used.get(ability_key)
        if not last_used:
            return True
        return (datetime.utcnow() - last_used).seconds >= ability.cooldown

    def _try_use_ability(self, pet: Pet) -> Optional[PetAbility]:
        """Try to use a random available ability"""
        available_abilities = [
            ability for ability in pet.abilities
            if self._can_use_ability(pet, ability)
        ]
        if not available_abilities:
            return None

        ability = random.choice(available_abilities)
        ability_key = f"{pet.pet_id}_{ability.name}"
        self.last_ability_used[ability_key] = datetime.utcnow()
        return ability

    def execute_round(self) -> Tuple[Optional[Pet], Dict[str, Any]]:
        """Execute a single battle round. Returns (winner, round_data)"""
        if self.state != BattleState.IN_PROGRESS:
            return None, {"error": "Battle not in progress"}

        self.current_round += 1
        if self.current_round > self.max_rounds:
            # Time limit reached - determine winner by remaining stats
            power1 = self.pet1.stats.calculate_power()
            power2 = self.pet2.stats.calculate_power()
            winner = self.pet1 if power1 > power2 else self.pet2
            return winner, {"reason": "time_limit"}

        # Determine turn order based on speed
        pets = [self.pet1, self.pet2]
        random.shuffle(pets)  # Random tiebreaker
        pets.sort(key=lambda p: p.stats.skill_levels["speed"], reverse=True)

        round_data = {"actions": []}
        
        # Execute turns
        for attacker in pets:
            defender = self.pet2 if attacker == self.pet1 else self.pet1
            
            # Try to use an ability
            ability = self._try_use_ability(attacker)
            damage = self._calculate_damage(attacker, defender, ability)
            
            # Record action
            action = {
                "attacker": attacker.pet_id,
                "defender": defender.pet_id,
                "damage": damage,
                "ability_used": ability.name if ability else None
            }
            round_data["actions"].append(action)
            
            # Apply damage
            defender_power = defender.stats.calculate_power()
            if damage >= defender_power:
                return attacker, round_data

        return None, round_data

    def start_battle(self) -> None:
        """Start the battle"""
        if self.state != BattleState.WAITING:
            return

        self.state = BattleState.IN_PROGRESS
        if self.event_manager:
            self.event_manager.emit(GameEvent(
                type=EventType.BATTLE_STARTED,
                user_id=str(self.pet1.owner_id),
                timestamp=datetime.utcnow(),
                data={
                    "battle_type": self.battle_type.value,
                    "pet1_id": self.pet1.pet_id,
                    "pet2_id": self.pet2.pet_id
                }
            ))

    def end_battle(self, winner: Pet) -> BattleResult:
        """End the battle and calculate rewards"""
        self.state = BattleState.FINISHED
        loser = self.pet2 if winner == self.pet1 else self.pet1

        # Calculate experience gain
        base_exp = 100
        level_diff_bonus = max(0, loser.stats.level - winner.stats.level) * 10
        battle_type_multiplier = {
            BattleType.FRIENDLY: 0.5,
            BattleType.RANKED: 1.0,
            BattleType.TOURNAMENT: 1.5,
            BattleType.CROSS_SYSTEM: 2.0
        }[self.battle_type]

        exp_gained = int((base_exp + level_diff_bonus) * battle_type_multiplier)

        # Award experience
        winner.stats.gain_exp(exp_gained, self.event_manager, {
            "pet_id": winner.pet_id,
            "owner_id": winner.owner_id,
            "origin": winner.origin,
            "battle_type": self.battle_type.value
        })

        # Create battle result
        result = BattleResult(
            winner=winner,
            loser=loser,
            battle_type=self.battle_type,
            rounds=self.current_round,
            exp_gained=exp_gained,
            ability_logs=self.ability_logs
        )

        # Emit battle completed event
        if self.event_manager:
            self.event_manager.emit(GameEvent(
                type=EventType.BATTLE_COMPLETED,
                user_id=str(winner.owner_id),
                timestamp=datetime.utcnow(),
                data={
                    "battle_type": self.battle_type.value,
                    "winner_id": winner.pet_id,
                    "loser_id": loser.pet_id,
                    "rounds": self.current_round,
                    "exp_gained": exp_gained
                }
            ))

        return result


class BattleManager:
    def __init__(self, event_manager: Optional[EventManager] = None):
        self.active_battles: Dict[str, Battle] = {}
        self.battle_history: List[BattleResult] = []
        self.event_manager = event_manager
        self.rankings: Dict[str, int] = {}  # pet_id -> ranking points

    def create_battle(self, pet1: Pet, pet2: Pet, battle_type: BattleType) -> str:
        """Create a new battle and return its ID"""
        battle_id = str(random.randint(10000, 99999))
        battle = Battle(pet1, pet2, battle_type, self.event_manager)
        self.active_battles[battle_id] = battle
        return battle_id

    def start_battle(self, battle_id: str) -> bool:
        """Start a battle by ID"""
        battle = self.active_battles.get(battle_id)
        if not battle or battle.state != BattleState.WAITING:
            return False
        battle.start_battle()
        return True

    def execute_battle(self, battle_id: str) -> Optional[BattleResult]:
        """Execute an entire battle until completion"""
        battle = self.active_battles.get(battle_id)
        if not battle or battle.state != BattleState.IN_PROGRESS:
            return None

        while True:
            winner, round_data = battle.execute_round()
            battle.ability_logs.append(round_data)
            
            if winner:
                result = battle.end_battle(winner)
                self.battle_history.append(result)
                del self.active_battles[battle_id]
                
                # Update rankings for ranked battles
                if battle.battle_type == BattleType.RANKED:
                    self._update_rankings(result)
                
                return result

    def _update_rankings(self, result: BattleResult) -> None:
        """Update rankings after a ranked battle"""
        winner_current = self.rankings.get(result.winner.pet_id, 1000)
        loser_current = self.rankings.get(result.loser.pet_id, 1000)
        
        # Simple ELO-like system
        k_factor = 32
        expected_winner = 1 / (1 + 10 ** ((loser_current - winner_current) / 400))
        
        winner_new = winner_current + k_factor * (1 - expected_winner)
        loser_new = loser_current + k_factor * (0 - (1 - expected_winner))
        
        self.rankings[result.winner.pet_id] = int(winner_new)
        self.rankings[result.loser.pet_id] = int(loser_new)

    def get_rankings(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get top ranked pets"""
        return sorted(self.rankings.items(), key=lambda x: x[1], reverse=True)[:limit]

    def get_battle_history(self, pet_id: Optional[str] = None, 
                          battle_type: Optional[BattleType] = None,
                          limit: int = 10) -> List[BattleResult]:
        """Get battle history with optional filters"""
        filtered = self.battle_history
        if pet_id:
            filtered = [r for r in filtered if r.winner.pet_id == pet_id or r.loser.pet_id == pet_id]
        if battle_type:
            filtered = [r for r in filtered if r.battle_type == battle_type]
        return sorted(filtered, key=lambda r: r.timestamp, reverse=True)[:limit]
