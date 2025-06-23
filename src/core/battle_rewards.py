"""Battle rewards and experience management."""

import random
from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.core.battle_manager import BattleType


@dataclass
class BattleReward:
    """Represents rewards from a battle."""

    xp: int
    coins: int
    items: Dict[str, int] = None  # item_id: quantity
    special_rewards: Dict[str, Any] = None


class BattleRewardsManager:
    """Manages battle rewards and experience across battle types."""

    def __init__(self):
        # Base XP values for each battle type
        self.base_xp = {
            BattleType.OSRS: 100,
            BattleType.POKEMON: 80,
            BattleType.PET: 60,
        }

        # Base coin rewards
        self.base_coins = {
            BattleType.OSRS: 50,
            BattleType.POKEMON: 40,
            BattleType.PET: 30,
        }

        # Special item drop chances per battle type
        self.item_chances = {
            BattleType.OSRS: {
                "rare_drop_table": 0.01,
                "combat_supplies": 0.05,
                "equipment": 0.03,
            },
            BattleType.POKEMON: {
                "rare_candy": 0.02,
                "evolution_stone": 0.01,
                "held_item": 0.04,
            },
            BattleType.PET: {"treat": 0.1, "toy": 0.05, "accessory": 0.02},
        }

    def calculate_rewards(
        self,
        battle_type: BattleType,
        winner_level: int,
        loser_level: int,
        battle_duration: int,
        special_conditions: Optional[Dict[str, Any]] = None,
    ) -> BattleReward:
        """Calculate battle rewards based on various factors."""
        # Get base values for battle type
        base_xp = self.base_xp[battle_type]
        base_coins = self.base_coins[battle_type]

        # Level difference modifier
        level_diff = abs(winner_level - loser_level)
        if winner_level < loser_level:
            # Bonus for beating higher level opponent
            level_mod = 1 + (level_diff * 0.1)
        else:
            # Reduced rewards for beating lower level opponent
            level_mod = max(0.5, 1 - (level_diff * 0.05))

        # Duration modifier (rewards longer battles)
        duration_mod = min(1.5, 1 + (battle_duration / 300))  # Cap at 1.5x for 5 min

        # Calculate final XP and coins
        xp = int(base_xp * level_mod * duration_mod)
        coins = int(base_coins * level_mod)

        # Roll for item drops
        items = {}
        for item_type, chance in self.item_chances[battle_type].items():
            if random.random() < chance:
                items[item_type] = 1  # Could add quantity variation

        # Apply any special conditions
        special_rewards = {}
        if special_conditions:
            if special_conditions.get("win_streak"):
                streak = special_conditions["win_streak"]
                streak_bonus = min(2.0, 1 + (streak * 0.1))  # Cap at 2x
                xp = int(xp * streak_bonus)
                coins = int(coins * streak_bonus)

            if special_conditions.get("first_win_of_day"):
                xp *= 2
                coins *= 2

            if special_conditions.get("event_bonus"):
                special_rewards["event_points"] = random.randint(10, 20)

        return BattleReward(
            xp=xp,
            coins=coins,
            items=items or None,
            special_rewards=special_rewards or None,
        )

    def apply_rewards(
        self,
        battle_type: BattleType,
        player_data: Dict[str, Any],
        rewards: BattleReward,
    ) -> Dict[str, Any]:
        """Apply rewards to player data based on battle type."""
        updated = player_data.copy()

        if battle_type == BattleType.OSRS:
            # Add XP to combat skills
            for skill in ["attack", "strength", "defence", "hitpoints"]:
                if skill in updated["skills"]:
                    updated["skills"][skill]["xp"] += rewards.xp
            updated["coins"] += rewards.coins

        elif battle_type == BattleType.POKEMON:
            # Add XP to active Pokemon
            if "active_pokemon" in updated:
                updated["active_pokemon"]["xp"] += rewards.xp
                # Check for evolution
                if self._check_evolution(updated["active_pokemon"]):
                    updated["active_pokemon"]["can_evolve"] = True
            updated["pokecoins"] += rewards.coins

        elif battle_type == BattleType.PET:
            # Add XP and loyalty to pet
            if "active_pet" in updated:
                updated["active_pet"]["xp"] += rewards.xp
                updated["active_pet"]["loyalty"] = min(100, updated["active_pet"]["loyalty"] + 5)
            updated["pet_tokens"] += rewards.coins

        # Add any items won
        if rewards.items:
            if "inventory" not in updated:
                updated["inventory"] = {}
            for item, qty in rewards.items.items():
                updated["inventory"][item] = updated["inventory"].get(item, 0) + qty

        # Add any special rewards
        if rewards.special_rewards:
            if "special_rewards" not in updated:
                updated["special_rewards"] = {}
            updated["special_rewards"].update(rewards.special_rewards)

        return updated

    def _check_evolution(self, pokemon_data: Dict[str, Any]) -> bool:
        """Check if a Pokemon is ready to evolve."""
        if (
            "evolution_level" in pokemon_data
            and pokemon_data["level"] >= pokemon_data["evolution_level"]
        ):
            return True
        return False
