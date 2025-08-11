"""Skill manager for handling skill actions and experience calculations."""

import math
import random
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .game_tick import GameTick, TickPriority


class SkillType(Enum):
    """Available skills in OSRS."""

    ATTACK = "attack"
    STRENGTH = "strength"
    DEFENCE = "defence"
    RANGED = "ranged"
    PRAYER = "prayer"
    MAGIC = "magic"
    RUNECRAFT = "runecraft"
    HITPOINTS = "hitpoints"
    CRAFTING = "crafting"
    MINING = "mining"
    SMITHING = "smithing"
    FISHING = "fishing"
    COOKING = "cooking"
    FIREMAKING = "firemaking"
    WOODCUTTING = "woodcutting"
    AGILITY = "agility"
    HERBLORE = "herblore"
    THIEVING = "thieving"
    FLETCHING = "fletching"
    SLAYER = "slayer"
    FARMING = "farming"
    CONSTRUCTION = "construction"
    HUNTER = "hunter"


@dataclass
class SkillAction:
    """Represents a skill training action."""

    skill: SkillType
    level_required: int
    base_xp: float
    ticks_per_action: int
    success_chance: float
    tool_required: Optional[str] = None
    resources_required: Dict[str, int] = None


class SkillManager:
    """Manages skill actions and experience calculations."""

    # Constants from OSRS
    MAX_LEVEL = 99
    MAX_VIRTUAL_LEVEL = 120
    MAX_XP = 200_000_000

    # Experience table (level: experience required)
    XP_TABLE = {
        1: 0,
        2: 83,
        3: 174,
        4: 276,
        5: 388,
        6: 512,
        7: 650,
        8: 801,
        9: 969,
        10: 1154,
        # ... continues to 99
        99: 13_034_431,
    }

    def __init__(self, game_tick: GameTick, database_manager):
        """Initialize skill manager.

        Args:
            game_tick: GameTick system instance
            database_manager: Database manager instance
        """
        self.game_tick = game_tick
        self.db = database_manager
        self.current_actions: Dict[int, SkillAction] = {}  # player_id: action
        self.action_progress: Dict[int, int] = {}  # player_id: ticks_remaining

        # Complete XP table
        self._complete_xp_table()

        # Register skill tick task
        self.game_tick.register_task("skill_update", self._skill_tick, TickPriority.SKILLS)

    def _complete_xp_table(self):
        """Fill in missing XP table values using OSRS formula."""
        for level in range(11, 100):
            if level not in self.XP_TABLE:
                points = math.floor(level - 1 + 300 * 2 ** ((level - 1) / 7))
                self.XP_TABLE[level] = math.floor(points / 4)

    async def _skill_tick(self):
        """Process skill actions for current game tick."""
        for player_id in list(self.current_actions.keys()):
            if player_id not in self.action_progress:
                continue

            action = self.current_actions[player_id]
            self.action_progress[player_id] -= 1

            if self.action_progress[player_id] <= 0:
                # Action complete, roll for success
                if random.random() < action.success_chance:
                    await self._complete_action(player_id, action)

                # Reset progress for continuous actions
                self.action_progress[player_id] = action.ticks_per_action

    async def _complete_action(self, player_id: int, action: SkillAction):
        """Complete a skill action and award experience.

        Args:
            player_id: Player's ID
            action: Completed skill action
        """
        # Get current skill stats
        current_level = await self.get_skill_level(player_id, action.skill)
        current_xp = await self.get_skill_xp(player_id, action.skill)

        # Calculate and award XP
        new_xp = min(self.MAX_XP, current_xp + action.base_xp)
        new_level = self.get_level_for_xp(new_xp)

        # Update database
        await self.db.update_player_stats(player_id, action.skill.value, new_level, new_xp)

    def start_action(self, player_id: int, action: SkillAction) -> Tuple[bool, Optional[str]]:
        """Start a skill training action.

        Args:
            player_id: Player's ID
            action: Skill action to perform

        Returns:
            Tuple of (success, error message if failed)
        """
        # Check if already training
        if player_id in self.current_actions:
            return (False, "Already performing an action")

        # Check level requirement
        current_level = self.get_skill_level(player_id, action.skill)
        if current_level < action.level_required:
            return (False, f"Requires {action.skill.value} level {action.level_required}")

        # Start action
        self.current_actions[player_id] = action
        self.action_progress[player_id] = action.ticks_per_action
        return (True, None)

    def stop_action(self, player_id: int):
        """Stop current skill action.

        Args:
            player_id: Player's ID
        """
        self.current_actions.pop(player_id, None)
        self.action_progress.pop(player_id, None)

    def get_level_for_xp(self, xp: float) -> int:
        """Get the level for a given amount of experience.

        Args:
            xp: The amount of experience

        Returns:
            The corresponding level (1-99)
        """
        for level in range(99, 0, -1):
            if xp >= self.XP_TABLE[level]:
                return level
        return 1

    def get_xp_for_level(self, level: int) -> float:
        """Get the minimum experience required for a level.

        Args:
            level: The target level (1-99)

        Returns:
            The required experience

        Raises:
            ValueError: If level is not between 1 and 99
        """
        if not 1 <= level <= 99:
            raise ValueError("Level must be between 1 and 99")
        return float(self.XP_TABLE[level])

    async def get_skill_level(self, player_id: int, skill: SkillType) -> int:
        """Get player's current level in a skill.

        Args:
            player_id: Player's ID
            skill: The skill to check

        Returns:
            Current skill level
        """
        try:
            result = await self.db.get_player_stat(player_id, skill.value)
            return result["level"] if result else 1
        except Exception:
            return 1

    async def get_skill_xp(self, player_id: int, skill: SkillType) -> float:
        """Get player's current experience in a skill.

        Args:
            player_id: Player's ID
            skill: The skill to check

        Returns:
            Current skill experience
        """
        try:
            result = await self.db.get_player_stat(player_id, skill.value)
            return result["experience"] if result else 0.0
        except Exception:
            return 0.0

    def calculate_success_chance(
        self, action: SkillAction, level: int, tool_bonus: int = 0
    ) -> float:
        """Calculate success chance for a skill action.

        Args:
            action: The skill action
            level: Current skill level
            tool_bonus: Bonus from equipment

        Returns:
            Success chance (0-1)
        """
        effective_level = level + tool_bonus
        level_difference = effective_level - action.level_required

        # Base formulas from OSRS
        if action.skill == SkillType.MINING:
            chance = (level_difference + 3) / 50
        elif action.skill == SkillType.FISHING:
            chance = (level_difference + 5) / 45
        elif action.skill == SkillType.WOODCUTTING:
            chance = (level_difference + 8) / 40
        elif action.skill == SkillType.THIEVING:
            chance = (level_difference + 1) / 35
        else:
            chance = 0.5 + level_difference / 100

        return min(0.95, max(0.05, chance))

    def calculate_action_interval(
        self, action: SkillAction, level: int, tool_bonus: int = 0
    ) -> int:
        """Calculate ticks between action attempts.

        Args:
            action: The skill action
            level: Current skill level
            tool_bonus: Bonus from equipment

        Returns:
            Number of ticks between attempts
        """
        effective_level = level + tool_bonus
        level_difference = effective_level - action.level_required

        # Base intervals from OSRS
        if action.skill == SkillType.MINING:
            base_ticks = 6
            reduction = min(3, level_difference // 10)
        elif action.skill == SkillType.FISHING:
            base_ticks = 5
            reduction = min(2, level_difference // 15)
        elif action.skill == SkillType.WOODCUTTING:
            base_ticks = 4
            reduction = min(2, level_difference // 12)
        else:
            base_ticks = action.ticks_per_action
            reduction = min(2, level_difference // 20)

        return max(1, base_ticks - reduction)
