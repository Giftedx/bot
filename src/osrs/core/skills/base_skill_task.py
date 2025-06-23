"""Base implementation for skilling tasks."""
from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Optional

from ..task import Task, TaskRequirements, TaskRewards
from ..constants import SkillType
from ...models.user import User


class BaseSkillTask(Task):
    """Base class for all skilling tasks."""

    def __init__(self, user: User, skill: SkillType):
        """Initialize skilling task."""
        self.skill = skill
        self.success_chance = 0.0
        self.ticks_per_action = 4  # Default 2.4 seconds per action
        self.actions_completed = 0
        self.actions_failed = 0
        super().__init__(user)

    @abstractmethod
    def calculate_success_chance(self) -> float:
        """Calculate chance of successful action."""
        pass

    @abstractmethod
    def calculate_xp_per_action(self) -> float:
        """Calculate XP gained per successful action."""
        pass

    @abstractmethod
    def get_base_ticks_per_action(self) -> int:
        """Get base number of game ticks per action."""
        pass

    def calculate_end_time(self) -> datetime:
        """Calculate task end time based on action time."""
        # Default to 5 minutes of skilling
        duration = timedelta(minutes=5)
        return datetime.now() + duration

    def tick(self) -> None:
        """Update task state for this game tick."""
        if self.status != self.status.RUNNING:
            return

        # Update success chance based on current stats/boosts
        self.success_chance = self.calculate_success_chance()

        # Only process on action ticks
        if self.actions_completed % self.ticks_per_action != 0:
            return

        # Attempt action
        if self.attempt_action():
            self.actions_completed += 1
            # Add XP for successful action
            xp = self.calculate_xp_per_action()
            self.user.skills[self.skill].add_xp(int(xp))
        else:
            self.actions_failed += 1

    def attempt_action(self) -> bool:
        """
        Attempt a skilling action.
        Returns True if successful.
        """
        import random

        return random.random() < self.success_chance

    @property
    def success_rate(self) -> float:
        """Calculate success rate of actions so far."""
        total = self.actions_completed + self.actions_failed
        if total == 0:
            return 0.0
        return self.actions_completed / total

    @property
    def xp_per_hour(self) -> float:
        """Calculate XP gained per hour at current rate."""
        if not self.duration:
            return 0.0

        hours = self.duration.total_seconds() / 3600
        if hours == 0:
            return 0.0

        total_xp = sum(self.calculate_xp_per_action() for _ in range(self.actions_completed))
        return total_xp / hours
