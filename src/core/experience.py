"""Core experience and leveling system."""

from enum import Enum
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
import math

from ..features.pets.event_system import EventManager, EventType, GameEvent
from .pet_system import Pet, PetOrigin


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


class ExperienceCalculator:
    def __init__(self):
        self.base_exp_rates = {"interaction": 20, "battle": 100, "training": 50, "achievement": 200}

        self.rarity_multipliers = {
            "common": 1.0,
            "uncommon": 1.2,
            "rare": 1.5,
            "epic": 2.0,
            "legendary": 3.0,
        }

    def calculate_exp_for_level(self, level: int) -> int:
        """Calculate experience needed for next level"""
        return int(100 * (level**1.5))

    def calculate_level_from_exp(self, exp: int) -> int:
        """Calculate level from total experience"""
        return int((exp / 100) ** (1 / 1.5))


class ExperienceManager:
    def __init__(self, event_manager: Optional[EventManager] = None):
        self.calculator = ExperienceCalculator()
        self.event_manager = event_manager
        self.exp_boosts: Dict[str, Dict[str, Any]] = {}  # pet_id -> boost data
        self.daily_exp_caps: Dict[str, Dict[str, Any]] = {}  # pet_id -> cap data

    def add_exp_boost(
        self,
        pet_id: str,
        boost_value: float,
        duration_hours: Optional[int] = None,
        source: Optional[str] = None,
    ) -> None:
        """Add an experience boost for a pet"""
        expires_at = None
        if duration_hours:
            expires_at = datetime.utcnow() + timedelta(hours=duration_hours)

        self.exp_boosts[pet_id] = {"value": boost_value, "expires_at": expires_at, "source": source}

    def get_active_boosts(self, pet_id: str) -> float:
        """Get total active experience boost for a pet"""
        now = datetime.utcnow()
        total_boost = 0.0

        if pet_id in self.exp_boosts:
            boost_data = self.exp_boosts[pet_id]
            if not boost_data["expires_at"] or boost_data["expires_at"] > now:
                total_boost += boost_data["value"]
            else:
                del self.exp_boosts[pet_id]

        return total_boost

    def set_daily_exp_cap(self, pet_id: str, cap: int) -> None:
        """Set daily experience cap for a pet"""
        self.daily_exp_caps[pet_id] = {
            "cap": cap,
            "gained_today": 0,
            "last_reset": datetime.utcnow(),
        }

    def can_gain_exp(self, pet_id: str, amount: int) -> bool:
        """Check if pet can gain experience (within daily cap)"""
        if pet_id not in self.daily_exp_caps:
            return True

        cap_data = self.daily_exp_caps[pet_id]
        now = datetime.utcnow()

        # Reset daily cap if it's a new day
        if (now - cap_data["last_reset"]).days >= 1:
            cap_data["gained_today"] = 0
            cap_data["last_reset"] = now

        return cap_data["gained_today"] + amount <= cap_data["cap"]

    def award_exp(
        self, pet: Pet, base_amount: int, source: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Award experience to a pet with boosts and caps applied"""
        if not self.can_gain_exp(pet.pet_id, base_amount):
            return {"gained": 0, "reason": "daily_cap_reached"}

        # Apply rarity multiplier
        rarity_mult = self.calculator.rarity_multipliers.get(pet.rarity.value, 1.0)
        amount = base_amount * rarity_mult

        # Apply active boosts
        boost = self.get_active_boosts(pet.pet_id)
        if boost > 0:
            amount *= 1 + boost

        # Apply cross-system bonuses
        if source == "battle" and metadata and "opponent_origin" in metadata:
            if (
                pet.origin == PetOrigin.OSRS
                and metadata["opponent_origin"] == PetOrigin.POKEMON.value
            ):
                amount *= 1.2  # Bonus for OSRS pets beating Pokemon
            elif (
                pet.origin == PetOrigin.POKEMON
                and metadata["opponent_origin"] == PetOrigin.OSRS.value
            ):
                amount *= 1.3  # Bigger bonus for Pokemon beating OSRS pets

        # Round and cap the final amount
        final_amount = min(int(amount), 1000)  # Cap at 1000 exp per action

        # Update daily cap if applicable
        if pet.pet_id in self.daily_exp_caps:
            self.daily_exp_caps[pet.pet_id]["gained_today"] += final_amount

        # Award experience and check for level up
        old_level = pet.stats.level
        leveled_up = pet.stats.gain_exp(
            final_amount,
            self.event_manager,
            {
                "pet_id": pet.pet_id,
                "owner_id": pet.owner_id,
                "origin": pet.origin,
                "source": source,
                **(metadata or {}),
            },
        )

        result = {
            "base_amount": base_amount,
            "rarity_multiplier": rarity_mult,
            "boost_multiplier": 1 + boost if boost > 0 else 1,
            "final_amount": final_amount,
            "leveled_up": leveled_up,
            "old_level": old_level,
            "new_level": pet.stats.level,
        }

        # Emit experience gained event
        if self.event_manager:
            self.event_manager.emit(
                GameEvent(
                    type=EventType.EXPERIENCE_GAINED,
                    user_id=str(pet.owner_id),
                    timestamp=datetime.utcnow(),
                    data={
                        "pet_id": pet.pet_id,
                        "pet_type": pet.origin.value,
                        "source": source,
                        "base_amount": base_amount,
                        "final_amount": final_amount,
                        "leveled_up": leveled_up,
                        "new_level": pet.stats.level,
                        **(metadata or {}),
                    },
                )
            )

        return result


class CrossSystemExperienceHandler:
    def __init__(self, exp_manager: ExperienceManager):
        self.exp_manager = exp_manager
        self.milestone_bonuses = {
            "osrs_combat": {
                50: {"value": 0.1, "duration": 24},  # 10% for 24h at combat 50
                99: {"value": 0.2, "duration": 48},  # 20% for 48h at combat 99
            },
            "pokemon_evolution": {
                3: {"value": 0.1, "duration": 24},  # 10% for 24h after 3 evolutions
                10: {"value": 0.2, "duration": 48},  # 20% for 48h after 10 evolutions
            },
        }

    def check_milestones(self, pet: Pet, stat_type: str, value: int) -> None:
        """Check and award milestone bonuses"""
        milestones = None
        if pet.origin == PetOrigin.OSRS and stat_type == "combat":
            milestones = self.milestone_bonuses["osrs_combat"]
        elif pet.origin == PetOrigin.POKEMON and stat_type == "evolutions":
            milestones = self.milestone_bonuses["pokemon_evolution"]

        if milestones and value in milestones:
            bonus = milestones[value]
            # Add boost to both OSRS and Pokemon pets
            for boost_pet_id in self.exp_manager.exp_boosts:
                self.exp_manager.add_exp_boost(
                    boost_pet_id,
                    bonus["value"],
                    bonus["duration"],
                    f"{pet.origin.value}_{stat_type}_milestone",
                )
