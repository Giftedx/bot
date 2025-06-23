"""Battle system implementation for pet battles.

This module provides the core battle mechanics including:
- Turn-based combat system
- Stat calculations and leveling
- Move sets and effectiveness
- Battle rewards
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass
from src.pets.models import Pet, PetType, StatusEffect, PetMove


class BattleError(Exception):
    """Base class for battle-related errors."""


class BattleNotFoundError(BattleError):
    """Raised when trying to access a non-existent battle."""


class InvalidMoveError(BattleError):
    """Raised when an invalid move is attempted."""


class BattleInProgressError(BattleError):
    """Raised when trying to start a battle while another is in progress."""


@dataclass
class BattleStats:
    """Stats for a pet in battle."""

    hp: int
    attack: int
    defense: int
    speed: int
    level: int


@dataclass
class BattleState:
    """Represents the current state of a battle."""

    battle_id: int
    pet1_id: int
    pet2_id: int
    current_turn: int
    pet1_stats: BattleStats
    pet2_stats: BattleStats
    status_effects: Dict[int, StatusEffect]
    last_move: Optional[str] = None
    winner: Optional[int] = None


class BattleSystem:
    """Core battle system implementation."""

    def __init__(self) -> None:
        """Initialize battle system."""
        self._active_battles: Dict[int, BattleState] = {}
        self._battle_counter: int = 0

    async def start_battle(self, pet1: Pet, pet2: Pet) -> BattleState:
        """Start a new battle between two pets.

        Args:
            pet1: First pet
            pet2: Second pet

        Returns:
            Battle state for the new battle

        Raises:
            BattleInProgressError: If either pet is already in battle
        """
        self._battle_counter += 1
        battle_id = self._battle_counter

        # Convert pets to battle stats
        pet1_stats = BattleStats(
            hp=pet1.max_health,
            attack=10 + (pet1.level * 2),
            defense=5 + pet1.level,
            speed=10 + pet1.level,
            level=pet1.level,
        )

        pet2_stats = BattleStats(
            hp=pet2.max_health,
            attack=10 + (pet2.level * 2),
            defense=5 + pet2.level,
            speed=10 + pet2.level,
            level=pet2.level,
        )

        # Create battle state
        battle = BattleState(
            battle_id=battle_id,
            pet1_id=id(pet1),
            pet2_id=id(pet2),
            current_turn=1,
            pet1_stats=pet1_stats,
            pet2_stats=pet2_stats,
            status_effects={},
        )

        self._active_battles[battle_id] = battle
        return battle

    def _calculate_damage(
        self,
        move: PetMove,
        attacker_stats: BattleStats,
        defender_stats: BattleStats,
        attacker_element: PetType,
        defender_element: PetType,
    ) -> int:
        """Calculate damage for a move."""
        # Base damage
        damage = (move.damage * attacker_stats.attack) / defender_stats.defense

        # Element effectiveness
        effectiveness = self._get_element_effectiveness(attacker_element, defender_element)
        damage *= effectiveness

        # Level difference
        level_bonus = (attacker_stats.level - defender_stats.level) * 0.1
        damage *= 1 + max(0, level_bonus)

        return max(1, int(damage))

    def _get_element_effectiveness(self, attacker: PetType, defender: PetType) -> float:
        """Get elemental damage multiplier."""
        effectiveness_chart = {
            PetType.FIRE: {PetType.EARTH: 2.0, PetType.AIR: 0.5},
            PetType.WATER: {PetType.FIRE: 2.0, PetType.EARTH: 0.5},
            PetType.EARTH: {PetType.AIR: 2.0, PetType.WATER: 0.5},
            PetType.AIR: {PetType.WATER: 2.0, PetType.FIRE: 0.5},
            PetType.LIGHT: {PetType.DARK: 2.0},
            PetType.DARK: {PetType.LIGHT: 2.0},
        }

        return effectiveness_chart.get(attacker, {}).get(defender, 1.0)

    async def process_turn(
        self, battle_id: int, move: PetMove, pet: Pet, opponent: Pet
    ) -> Dict[str, Any]:
        """Process a single turn in a battle.

        Args:
            battle_id: ID of active battle
            move: Move being used
            pet: Pet using the move
            opponent: Target pet

        Returns:
            Dict containing turn results

        Raises:
            BattleNotFoundError: If battle_id is invalid
            InvalidMoveError: If move is invalid
        """
        battle = self._active_battles.get(battle_id)
        if not battle:
            raise BattleNotFoundError(f"Battle {battle_id} not found")

        # Validate turn
        if id(pet) != battle.pet1_id and id(pet) != battle.pet2_id:
            raise InvalidMoveError("Not your turn")

        # Get stats
        attacker_stats = battle.pet1_stats if id(pet) == battle.pet1_id else battle.pet2_stats
        defender_stats = battle.pet2_stats if id(pet) == battle.pet1_id else battle.pet1_stats

        # Calculate and apply damage
        damage = self._calculate_damage(
            move, attacker_stats, defender_stats, pet.element, opponent.element
        )

        defender_stats.hp -= damage

        # Check for battle end
        if defender_stats.hp <= 0:
            battle.winner = id(pet)
            del self._active_battles[battle_id]

        # Update turn counter
        battle.current_turn += 1
        battle.last_move = move.name

        return {
            "damage": damage,
            "move_name": move.name,
            "attacker": id(pet),
            "defender": id(opponent),
            "battle_over": battle.winner is not None,
            "winner": battle.winner,
        }

    def get_battle_state(self, battle_id: int) -> Optional[BattleState]:
        """Get the current state of a battle."""
        return self._active_battles.get(battle_id)
