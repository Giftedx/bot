"""Unified battle system manager."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from src.core.experience import ExperienceSystem, GameSystem


class BattleType(Enum):
    """Types of battles available."""

    OSRS = "osrs"
    POKEMON = "pokemon"
    PET = "pet"


@dataclass
class BattleReward:
    """Rewards from battle completion."""

    xp: int
    coins: int
    items: Optional[Dict[str, int]] = None
    special_rewards: Optional[Dict[str, Any]] = None


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
    battle_data: Dict[str, Any] = None


class BattleManager:
    """Manages all battle types and interactions."""

    def __init__(self, experience_system: ExperienceSystem):
        self.exp_system = experience_system
        self.active_battles: Dict[str, BattleState] = {}
        self._battle_counter = 0

        # Battle reward configurations
        self.reward_configs = {
            BattleType.OSRS: {
                "base_xp": 100,
                "base_coins": 50,
                "win_multiplier": 2.0,
                "loss_multiplier": 0.5,
            },
            BattleType.POKEMON: {
                "base_xp": 80,
                "base_coins": 40,
                "win_multiplier": 1.8,
                "loss_multiplier": 0.6,
            },
            BattleType.PET: {
                "base_xp": 60,
                "base_coins": 30,
                "win_multiplier": 1.5,
                "loss_multiplier": 0.7,
            },
        }

    def create_battle(
        self,
        battle_type: BattleType,
        challenger_id: int,
        opponent_id: int,
        initial_data: Dict[str, Any],
    ) -> BattleState:
        """Create a new battle."""
        self._battle_counter += 1
        battle_id = f"{battle_type.value}_{self._battle_counter}"

        state = BattleState(
            battle_id=battle_id,
            battle_type=battle_type,
            challenger_id=challenger_id,
            opponent_id=opponent_id,
            current_turn=challenger_id,
            battle_data=initial_data,
        )

        self.active_battles[battle_id] = state
        return state

    def end_battle(
        self, battle_state: BattleState, winner_id: int, loser_id: int
    ) -> Tuple[BattleReward, BattleReward]:
        """End a battle and calculate rewards."""
        if battle_state.battle_id not in self.active_battles:
            raise ValueError("Battle not found")

        config = self.reward_configs[battle_state.battle_type]

        # Calculate winner rewards
        winner_reward = BattleReward(
            xp=int(config["base_xp"] * config["win_multiplier"]),
            coins=int(config["base_coins"] * config["win_multiplier"]),
        )

        # Calculate loser rewards
        loser_reward = BattleReward(
            xp=int(config["base_xp"] * config["loss_multiplier"]),
            coins=int(config["base_coins"] * config["loss_multiplier"]),
        )

        # Update battle state
        battle_state.is_finished = True
        battle_state.winner_id = winner_id

        # Convert battle type to game system for XP calculations
        game_system = GameSystem[battle_state.battle_type.name]

        # Apply any cross-game bonuses
        winner_level = self.exp_system.calculate_level_from_xp(
            winner_reward.xp, game_system
        )
        loser_level = self.exp_system.calculate_level_from_xp(
            loser_reward.xp, game_system
        )

        # Cross-game bonus based on levels
        bonus = self.exp_system.calculate_cross_game_bonus(
            game_system, game_system, winner_level, loser_level  # Same system for now
        )

        winner_reward.xp = int(winner_reward.xp * bonus)

        del self.active_battles[battle_state.battle_id]
        return winner_reward, loser_reward

    def get_battle(self, battle_id: str) -> Optional[BattleState]:
        """Get battle state by ID."""
        return self.active_battles.get(battle_id)

    def get_active_battles(self, player_id: int) -> Dict[str, BattleState]:
        """Get all active battles for a player."""
        return {
            bid: state
            for bid, state in self.active_battles.items()
            if player_id in (state.challenger_id, state.opponent_id)
        }
