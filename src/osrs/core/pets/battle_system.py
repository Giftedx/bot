"""Unified battle system for pet battles."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import random
import uuid

from .base_models import BasePet, StatusEffect


@dataclass
class BattleStats:
    """Battle-specific stats for a pet."""

    current_hp: int
    max_hp: int
    attack: int
    defense: int
    speed: int
    energy: int = 100
    energy_regen: int = 10
    stat_modifiers: Dict[str, int] = field(
        default_factory=lambda: {"attack": 0, "defense": 0, "speed": 0}
    )


@dataclass
class BattleMove:
    """Represents a battle move/ability."""

    name: str
    power: int
    energy_cost: int
    accuracy: int
    element: str
    status_effect: Optional[StatusEffect] = None
    status_chance: int = 0
    cooldown: int = 0
    current_cooldown: int = 0


@dataclass
class BattlePet:
    """Pet state during battle."""

    pet: BasePet
    stats: BattleStats
    moves: List[BattleMove]
    status_effects: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class Battle:
    """Represents an active battle between pets."""

    id: str
    pet1: BattlePet
    pet2: BattlePet
    current_turn: int = 1
    max_turns: int = 50
    is_finished: bool = False
    winner: Optional[BattlePet] = None
    battle_log: List[Dict[str, Any]] = field(default_factory=list)


class BattleSystem:
    """Core battle system implementation."""

    def __init__(self):
        self.active_battles: Dict[str, Battle] = {}
        self.battle_history: List[Battle] = []

        # Element effectiveness chart
        self.element_chart = {
            "fire": {"earth": 2.0, "ice": 2.0, "nature": 0.5, "water": 0.5},
            "water": {"fire": 2.0, "earth": 0.5, "lightning": 0.5},
            "earth": {"lightning": 2.0, "water": 2.0, "fire": 0.5},
            "air": {"earth": 2.0, "lightning": 0.5},
            "lightning": {"water": 2.0, "air": 2.0, "earth": 0.5},
            "light": {"dark": 2.0, "shadow": 0.5},
            "dark": {"light": 2.0, "psychic": 2.0},
        }

        # Status effect definitions
        self.status_effects = {
            "burn": {"dot": 5, "turns": 3, "stat_mod": {"attack": 0.8}},  # Damage over time
            "poison": {"dot": 8, "turns": 3, "stat_mod": {"defense": 0.9}},
            "stun": {"skip_turn": True, "turns": 1},
            "weakness": {"stat_mod": {"attack": 0.75}, "turns": 2},
            "vulnerable": {"stat_mod": {"defense": 0.75}, "turns": 2},
        }

    def create_battle(self, pet1: BasePet, pet2: BasePet) -> Battle:
        """Create a new battle between two pets."""
        # Convert pets to battle format
        battle_pet1 = self._prepare_pet_for_battle(pet1)
        battle_pet2 = self._prepare_pet_for_battle(pet2)

        # Create battle
        battle = Battle(id=str(uuid.uuid4()), pet1=battle_pet1, pet2=battle_pet2)

        self.active_battles[battle.id] = battle
        return battle

    def _prepare_pet_for_battle(self, pet: BasePet) -> BattlePet:
        """Convert a pet to battle format with appropriate stats."""
        # Calculate battle stats
        base_hp = 50 + (pet.stats.level * 5)
        stats = BattleStats(
            current_hp=base_hp,
            max_hp=base_hp,
            attack=10 + (pet.stats.skill_levels["attack"] * 2),
            defense=5 + pet.stats.skill_levels["defense"],
            speed=8 + pet.stats.skill_levels["speed"],
        )

        # Convert abilities to battle moves
        moves = [
            BattleMove(
                name=ability.name,
                power=int(ability.effect_value * 10),
                energy_cost=20,
                accuracy=90,
                element=ability.effect_type,
                cooldown=ability.cooldown,
            )
            for ability in pet.abilities
        ]

        # Add basic attack if no moves
        if not moves:
            moves.append(
                BattleMove(
                    name="Basic Attack", power=10, energy_cost=10, accuracy=95, element="normal"
                )
            )

        return BattlePet(pet=pet, stats=stats, moves=moves)

    def process_turn(self, battle_id: str, attacker_move: str) -> Dict[str, Any]:
        """Process a single turn in a battle."""
        battle = self.active_battles.get(battle_id)
        if not battle or battle.is_finished:
            return {"error": "Invalid or finished battle"}

        # Get attacker and defender
        attacker = battle.pet1 if battle.current_turn % 2 == 1 else battle.pet2
        defender = battle.pet2 if battle.current_turn % 2 == 1 else battle.pet1

        # Get move
        move = next((m for m in attacker.moves if m.name == attacker_move), None)
        if not move:
            return {"error": "Invalid move"}

        # Check energy
        if attacker.stats.energy < move.energy_cost:
            return {"error": "Not enough energy"}

        # Check cooldown
        if move.current_cooldown > 0:
            return {"error": "Move on cooldown"}

        # Process status effects
        status_message = self._process_status_effects(attacker, defender)

        # Calculate accuracy
        if random.randint(1, 100) > move.accuracy:
            battle.battle_log.append(
                {
                    "turn": battle.current_turn,
                    "attacker": attacker.pet.name,
                    "move": move.name,
                    "result": "missed",
                }
            )
            return {"message": f"{attacker.pet.name}'s {move.name} missed!"}

        # Calculate and apply damage
        damage, effect_message = self._calculate_damage(move, attacker, defender)
        defender.stats.current_hp = max(0, defender.stats.current_hp - damage)

        # Apply energy cost
        attacker.stats.energy -= move.energy_cost

        # Apply move cooldown
        move.current_cooldown = move.cooldown

        # Check for battle end
        if defender.stats.current_hp <= 0:
            battle.is_finished = True
            battle.winner = attacker

        # Log turn
        battle.battle_log.append(
            {
                "turn": battle.current_turn,
                "attacker": attacker.pet.name,
                "move": move.name,
                "damage": damage,
                "status_effect": effect_message,
            }
        )

        # Update turn counter
        battle.current_turn += 1

        # Check turn limit
        if battle.current_turn > battle.max_turns:
            battle.is_finished = True
            # Winner is pet with most HP percentage remaining
            pet1_hp_pct = battle.pet1.stats.current_hp / battle.pet1.stats.max_hp
            pet2_hp_pct = battle.pet2.stats.current_hp / battle.pet2.stats.max_hp
            battle.winner = battle.pet1 if pet1_hp_pct > pet2_hp_pct else battle.pet2

        return {
            "damage": damage,
            "effect_message": effect_message,
            "status_message": status_message,
            "battle_over": battle.is_finished,
            "winner": battle.winner.pet.name if battle.winner else None,
        }

    def _calculate_damage(
        self, move: BattleMove, attacker: BattlePet, defender: BattlePet
    ) -> Tuple[int, str]:
        """Calculate damage for a move."""
        messages = []

        # Base damage
        damage = move.power * (attacker.stats.attack / defender.stats.defense)

        # Apply stat modifiers
        attack_mod = self._get_stat_modifier(attacker.stats.stat_modifiers["attack"])
        defense_mod = self._get_stat_modifier(defender.stats.stat_modifiers["defense"])
        damage *= attack_mod / defense_mod

        # Element effectiveness
        if move.element in self.element_chart:
            for defender_element, multiplier in self.element_chart[move.element].items():
                if defender_element in defender.pet.attributes.get("elements", []):
                    damage *= multiplier
                    if multiplier > 1:
                        messages.append("It's super effective!")
                    elif multiplier < 1:
                        messages.append("It's not very effective...")

        # Critical hit (10% chance)
        if random.random() < 0.1:
            damage *= 1.5
            messages.append("Critical hit!")

        # Apply status effect
        if move.status_effect and random.randint(1, 100) <= move.status_chance:
            if move.status_effect.value in self.status_effects:
                defender.status_effects[move.status_effect.value] = self.status_effects[
                    move.status_effect.value
                ].copy()
                messages.append(f"Applied {move.status_effect.value}!")

        return int(damage), " ".join(messages)

    def _process_status_effects(self, attacker: BattlePet, defender: BattlePet) -> str:
        """Process status effects and return message."""
        messages = []

        # Process attacker status effects
        for status, data in list(attacker.status_effects.items()):
            # Apply damage over time
            if "dot" in data:
                damage = data["dot"]
                attacker.stats.current_hp -= damage
                messages.append(f"{attacker.pet.name} took {damage} damage from {status}!")

            # Decrement duration
            data["turns"] -= 1
            if data["turns"] <= 0:
                del attacker.status_effects[status]
                messages.append(f"{attacker.pet.name} recovered from {status}!")

        return "\n".join(messages)

    def _get_stat_modifier(self, stages: int) -> float:
        """Get multiplier for stat stages (-6 to +6)."""
        if stages > 0:
            return (2 + stages) / 2
        return 2 / (2 - stages)

    def get_battle(self, battle_id: str) -> Optional[Battle]:
        """Get a battle by ID."""
        return self.active_battles.get(battle_id)

    def end_battle(self, battle_id: str) -> None:
        """End a battle and clean up."""
        if battle := self.active_battles.pop(battle_id, None):
            self.battle_history.append(battle)

    def get_available_moves(self, battle_id: str, pet_id: str) -> List[str]:
        """Get available moves for a pet in battle."""
        battle = self.active_battles.get(battle_id)
        if not battle:
            return []

        # Find the pet
        pet = None
        if battle.pet1.pet.id == pet_id:
            pet = battle.pet1
        elif battle.pet2.pet.id == pet_id:
            pet = battle.pet2

        if not pet:
            return []

        # Return moves that are off cooldown and have enough energy
        return [
            move.name
            for move in pet.moves
            if move.current_cooldown <= 0 and pet.stats.energy >= move.energy_cost
        ]
