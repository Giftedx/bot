"""Battle system configuration and settings."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from .models import BattleType


@dataclass
class BattleRewardConfig:
    """Configuration for battle rewards."""

    base_xp: int
    base_coins: int
    win_multiplier: float
    loss_multiplier: float
    streak_bonus: Optional[float] = None
    rare_drop_chance: Optional[float] = None
    evolution_chance: Optional[float] = None
    catch_bonus: Optional[float] = None
    loyalty_gain: Optional[int] = None
    training_bonus: Optional[float] = None


@dataclass
class BattleSystemConfig:
    """Global battle system configuration."""

    # Battle state settings
    max_turns_per_battle: int = 50
    turn_timeout_seconds: int = 30
    max_active_battles_per_player: int = 1

    # Resource settings
    base_energy_regen: int = 5
    base_hp_regen: int = 0
    max_status_effects: int = 3
    max_stat_stage: int = 6
    min_stat_stage: int = -6

    # Storage settings
    battle_storage_dir: str = "data/battles"
    battle_log_dir: str = "logs/battles"
    cleanup_age_hours: int = 24

    # Rate limiting
    moves_per_minute: int = 20
    battles_per_hour: int = 10


# Default reward configurations per battle type
DEFAULT_REWARD_CONFIGS: Dict[BattleType, BattleRewardConfig] = {
    BattleType.OSRS: BattleRewardConfig(
        base_xp=100,
        base_coins=50,
        win_multiplier=2.0,
        loss_multiplier=0.5,
        streak_bonus=0.1,
        rare_drop_chance=0.01,
    ),
    BattleType.POKEMON: BattleRewardConfig(
        base_xp=80,
        base_coins=40,
        win_multiplier=1.8,
        loss_multiplier=0.6,
        evolution_chance=0.05,
        catch_bonus=0.1,
    ),
    BattleType.PET: BattleRewardConfig(
        base_xp=60,
        base_coins=30,
        win_multiplier=1.5,
        loss_multiplier=0.7,
        loyalty_gain=5,
        training_bonus=0.15,
    ),
}

# Stat stage multipliers
STAT_STAGE_MULTIPLIERS: Dict[int, float] = {
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

# Status effects that prevent moves
MOVE_PREVENTING_STATUS: List[str] = ["frozen", "paralyzed", "stunned", "sleeping"]

# Required stats per battle type
REQUIRED_STATS: Dict[BattleType, List[str]] = {
    BattleType.OSRS: [
        "attack",
        "strength",
        "defense",
        "hitpoints",
        "prayer",
        "magic",
        "ranged",
    ],
    BattleType.POKEMON: [
        "hp",
        "attack",
        "defense",
        "special_attack",
        "special_defense",
        "speed",
    ],
    BattleType.PET: ["hp", "energy", "attack", "defense", "agility"],
}

# Resource types per battle type
RESOURCE_TYPES: Dict[BattleType, List[str]] = {
    BattleType.OSRS: ["prayer", "special_attack"],
    BattleType.POKEMON: ["pp"],
    BattleType.PET: ["energy", "stamina"],
}

# Default battle state initialization
DEFAULT_BATTLE_STATE = {
    "status_effects": [],
    "stat_stages": {"attack": 0, "defense": 0, "speed": 0, "accuracy": 0, "evasion": 0},
}

# Error messages
ERROR_MESSAGES = {
    "invalid_move": "Invalid move: {move}. Available moves: {available}",
    "insufficient_resource": "Insufficient {resource} for {move}: need {cost}, have {current}",
    "prevented_by_status": "Cannot use {move} while {status}",
    "battle_finished": "Battle is already finished",
    "not_your_turn": "Not your turn!",
    "battle_not_found": "Battle not found: {battle_id}",
    "player_in_battle": "Player is already in a battle",
    "rate_limit": "Too many {action} attempts. Please wait {wait_time} seconds.",
}
