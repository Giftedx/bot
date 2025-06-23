"""Pet battle system models."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PetType(Enum):
    """Pet element types."""

    FIRE = "🔥"
    WATER = "💧"
    EARTH = "🌍"
    AIR = "💨"
    LIGHT = "✨"
    DARK = "🌑"


class StatusEffect(Enum):
    """Battle status effects."""

    BURN = "🔥"
    POISON = "🤢"
    PARALYZE = "⚡"
    SLEEP = "💤"
    NONE = ""


@dataclass
class PetMove:
    """Represents a battle move/ability."""

    name: str
    damage: int
    element: PetType
    accuracy: int
    cooldown: int
    emoji: str
    status_effect: StatusEffect = StatusEffect.NONE
    status_chance: int = 0
    current_cooldown: int = 0


@dataclass
class Pet:
    """Base pet class."""

    id: int
    name: str
    owner_id: int
    element: PetType
    level: int = 1
    experience: int = 0
    max_hp: int = 100
    base_damage: int = 10
    moves: List[PetMove] = field(default_factory=list)


@dataclass
class BattlePet:
    """Pet state during battle."""

    pet: Pet
    moves: List[PetMove]
    current_hp: int
    max_hp: int
    element: PetType
    status: StatusEffect = StatusEffect.NONE
    status_turns: int = 0


@dataclass
class Battle:
    """Represents an active battle between pets."""

    id: int
    pet1: BattlePet
    pet2: BattlePet
    current_turn: int = 1
    last_move: Optional[PetMove] = None
    is_finished: bool = False
    winner: Optional[BattlePet] = None
