"""Core battle management system."""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


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


class BattleManager:
    """Manages all battle types and interactions."""

    def __init__(self) -> None:
        self.active_battles: Dict[str, BattleState] = {}
        self._battle_counter = 0

        # Battle reward configurations
        self.reward_configs = {
            BattleType.OSRS: {
                "base_xp": 100,
                "base_coins": 50,
                "win_multiplier": 2.0,
                "loss_multiplier": 0.5,
                "streak_bonus": 0.1,
                "rare_drop_chance": 0.01,
            },
            BattleType.POKEMON: {
                "base_xp": 80,
                "base_coins": 40,
                "win_multiplier": 1.8,
                "loss_multiplier": 0.6,
                "evolution_chance": 0.05,
                "catch_bonus": 0.1,
            },
            BattleType.PET: {
                "base_xp": 60,
                "base_coins": 30,
                "win_multiplier": 1.5,
                "loss_multiplier": 0.7,
                "loyalty_gain": 5,
                "training_bonus": 0.15,
            },
        }

    def create_battle(
        self,
        battle_type: BattleType,
        challenger_id: int,
        opponent_id: int,
        initial_data: Dict[str, Any],
    ) -> BattleState:
        """Create a new battle session."""
        self._battle_counter += 1
        battle_id = f"{battle_type.value}_{self._battle_counter}"

        battle = BattleState(
            battle_id=battle_id,
            battle_type=battle_type,
            challenger_id=challenger_id,
            opponent_id=opponent_id,
            current_turn=challenger_id,
            battle_data=initial_data,
        )

        self.active_battles[battle_id] = battle
        return battle

    def end_battle(
        self, battle_id: str, winner_id: Optional[int]
    ) -> Tuple[Optional[BattleReward], Optional[BattleReward]]:
        """End a battle and calculate rewards."""
        battle = self.active_battles.get(battle_id)
        if not battle:
            return None, None

        config = self.reward_configs[battle.battle_type]

        # Calculate winner rewards
        if winner_id:
            winner_reward = BattleReward(
                xp=int(config["base_xp"] * config["win_multiplier"]),
                coins=int(config["base_coins"] * config["win_multiplier"]),
            )

            # Determine loser
            loser_id = (
                battle.opponent_id
                if winner_id == battle.challenger_id
                else battle.challenger_id
            )

            loser_reward = BattleReward(
                xp=int(config["base_xp"] * config["loss_multiplier"]),
                coins=int(config["base_coins"] * config["loss_multiplier"]),
            )

            # Apply special rewards based on battle type
            self._apply_special_rewards(
                battle.battle_type, winner_reward, loser_reward, battle.battle_data
            )
        else:
            # Draw - both get partial rewards
            winner_reward = loser_reward = BattleReward(
                xp=int(config["base_xp"] * 0.75), coins=int(config["base_coins"] * 0.75)
            )

        battle.is_finished = True
        battle.winner_id = winner_id

        # Clean up
        del self.active_battles[battle_id]

        return winner_reward, loser_reward

    def get_battle(self, battle_id: str) -> Optional[BattleState]:
        """Get battle state by ID."""
        return self.active_battles.get(battle_id)

    def get_player_battle(self, player_id: int) -> Optional[BattleState]:
        """Get active battle for a player."""
        return next(
            (
                battle
                for battle in self.active_battles.values()
                if player_id in (battle.challenger_id, battle.opponent_id)
            ),
            None,
        )

    def record_turn(self, battle_id: str, move: str, results: Dict[str, Any]) -> None:
        """Record a turn in battle history."""
        if battle := self.active_battles.get(battle_id):
            battle.turn_history.append(
                {
                    "round": battle.round_number,
                    "player_id": battle.current_turn,
                    "move": move,
                    "results": results,
                }
            )
            battle.round_number += 1

    def _apply_special_rewards(
        self,
        battle_type: BattleType,
        winner_reward: BattleReward,
        loser_reward: BattleReward,
        battle_data: Dict[str, Any],
    ) -> None:
        """Apply battle type specific rewards."""
        config = self.reward_configs[battle_type]

        if battle_type == BattleType.OSRS:
            # Chance for rare drops
            if random.random() < config["rare_drop_chance"]:
                winner_reward.items = {"rare_drop": 1}

        elif battle_type == BattleType.POKEMON:
            # Evolution chance and catch bonus
            winner_reward.special_rewards = {
                "evolution_chance": config["evolution_chance"],
                "catch_bonus": config["catch_bonus"],
            }

        elif battle_type == BattleType.PET:
            # Loyalty and training bonuses
            winner_reward.special_rewards = {
                "loyalty_gain": config["loyalty_gain"],
                "training_bonus": config["training_bonus"],
            }
            loser_reward.special_rewards = {"loyalty_gain": config["loyalty_gain"] // 2}
