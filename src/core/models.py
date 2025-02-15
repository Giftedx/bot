"""Core models and data structures for battle system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class BattleType(Enum):
    """Types of battles available."""

    OSRS = "osrs"
    POKEMON = "pokemon"
    PET = "pet"


@dataclass
class BattleState:
    """Current state of an active battle."""

    battle_id: str
    battle_type: BattleType
    challenger_id: int
    opponent_id: int
    current_turn: int
    is_finished: bool = False
    winner_id: Optional[int] = None
    battle_data: Dict[str, Any] = field(default_factory=dict)
    turn_history: List[Dict[str, Any]] = field(default_factory=list)
    round_number: int = 1


@dataclass
class BattleReward:
    """Rewards from battle completion."""

    xp: int
    coins: int
    items: Optional[Dict[str, int]] = None
    special_rewards: Optional[Dict[str, Any]] = None


@dataclass
class StatusEffect:
    """Status effect applied to battler."""

    name: str
    duration: int
    effect_type: str
    magnitude: float
    description: str
    prevents_moves: bool = False
    dot_damage: Optional[int] = None
    stat_modifiers: Optional[Dict[str, float]] = None


@dataclass
class BattleMove:
    """Battle move definition."""

    name: str
    move_type: str
    base_power: int
    accuracy: int
    energy_cost: Optional[int] = None
    hp_cost: Optional[int] = None
    resource_cost: Optional[Dict[str, int]] = None
    status_effects: Optional[List[StatusEffect]] = None
    stat_changes: Optional[Dict[str, int]] = None
    priority: int = 0
