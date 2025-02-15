"""Core experience and leveling system."""

from enum import Enum
from typing import Dict, Optional


class GameSystem(Enum):
    """Game systems that use experience."""

    OSRS = "osrs"
    POKEMON = "pokemon"
    PET = "pet"


class ExperienceSystem:
    """Centralized experience calculation system."""

    # XP curve configuration per system
    XP_CONFIGS = {
        GameSystem.OSRS: {
            "base_multiplier": 4.0,
            "level_scaling": 7.0,
            "max_level": 99,
            "economy_rate": 100,  # Coins per level
        },
        GameSystem.POKEMON: {
            "base_multiplier": 2.5,
            "level_scaling": 3.0,
            "max_level": 100,
            "economy_rate": 150,  # Coins per level
        },
        GameSystem.PET: {
            "base_multiplier": 1.5,
            "level_scaling": 2.0,
            "max_level": 50,
            "economy_rate": 200,  # Coins per level
        },
    }

    # Cross-game bonus multipliers
    CROSS_GAME_BONUSES = {
        GameSystem.OSRS: {
            GameSystem.POKEMON: 1.1,  # 10% bonus to Pokemon XP if OSRS level is higher
            GameSystem.PET: 1.15,  # 15% bonus to Pet XP if OSRS level is higher
        },
        GameSystem.POKEMON: {
            GameSystem.OSRS: 1.05,  # 5% bonus to OSRS XP if Pokemon level is higher
            GameSystem.PET: 1.2,  # 20% bonus to Pet XP if Pokemon level is higher
        },
        GameSystem.PET: {
            GameSystem.OSRS: 1.1,  # 10% bonus to OSRS XP if Pet level is higher
            GameSystem.POKEMON: 1.15,  # 15% bonus to Pokemon XP if Pet level is higher
        },
    }

    @staticmethod
    def calculate_xp_for_level(level: int, system: GameSystem) -> int:
        """Calculate XP required for a specific level."""
        config = ExperienceSystem.XP_CONFIGS[system]
        if level >= config["max_level"]:
            return float("inf")

        # Base XP formula similar to OSRS but configurable
        total = 0
        for i in range(1, level):
            total += int(i + 300 * pow(2, i / config["level_scaling"]))
        return int(total / config["base_multiplier"])

    @staticmethod
    def calculate_level_from_xp(xp: int, system: GameSystem) -> int:
        """Calculate level based on total XP."""
        for level in range(1, ExperienceSystem.XP_CONFIGS[system]["max_level"] + 1):
            if xp < ExperienceSystem.calculate_xp_for_level(level, system):
                return level - 1
        return ExperienceSystem.XP_CONFIGS[system]["max_level"]

    @staticmethod
    def calculate_xp_gain(
        action_base_xp: float,
        level: int,
        system: GameSystem,
        modifiers: Optional[Dict[str, float]] = None,
    ) -> int:
        """Calculate XP gain for an action with modifiers."""
        if modifiers is None:
            modifiers = {}

        # Base XP scaled by level
        xp = action_base_xp * (1 + (level * 0.1))

        # Apply modifiers multiplicatively
        for modifier in modifiers.values():
            xp *= modifier

        return max(1, int(xp))

    @staticmethod
    def calculate_cross_game_bonus(
        source_system: GameSystem,
        target_system: GameSystem,
        source_level: int,
        target_level: int,
    ) -> float:
        """Calculate cross-game bonus multiplier.

        Args:
            source_system: System providing the bonus
            target_system: System receiving the bonus
            source_level: Level in source system
            target_level: Level in target system

        Returns:
            float: XP multiplier (1.0 = no bonus)
        """
        if source_level <= target_level:
            return 1.0

        base_bonus = ExperienceSystem.CROSS_GAME_BONUSES.get(source_system, {}).get(
            target_system, 1.0
        )

        # Scale bonus by level difference up to 50% of base bonus
        level_diff_bonus = min((source_level - target_level) * 0.01, base_bonus * 0.5)

        return base_bonus + level_diff_bonus

    @staticmethod
    def calculate_coin_reward(
        level_gained: int,
        system: GameSystem,
        modifiers: Optional[Dict[str, float]] = None,
    ) -> int:
        """Calculate coin reward for leveling up.

        Args:
            level_gained: New level achieved
            system: Game system
            modifiers: Economy modifiers (events, bonuses, etc)

        Returns:
            int: Coin reward amount
        """
        if modifiers is None:
            modifiers = {}

        base_reward = ExperienceSystem.XP_CONFIGS[system]["economy_rate"] * level_gained

        # Apply modifiers
        for modifier in modifiers.values():
            base_reward *= modifier

        return max(1, int(base_reward))
