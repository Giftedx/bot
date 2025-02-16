"""OSRS task system implementation."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Union, Any
from enum import Enum, auto

from .bank import Bank
from .constants import SkillType
from ..models.user import User


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class TaskRequirements:
    """Requirements for starting a task."""
    skills: Dict[SkillType, int] = field(default_factory=dict)
    items: Dict[Union[str, int], int] = field(default_factory=dict)
    quests: Set[str] = field(default_factory=set)
    combat_level: Optional[int] = None
    gp: int = 0


@dataclass
class TaskRewards:
    """Rewards for completing a task."""
    xp: Dict[SkillType, int] = field(default_factory=dict)
    items: Dict[Union[str, int], int] = field(default_factory=dict)
    gp: int = 0


class Task(ABC):
    """Base class for all OSRS tasks."""

    def __init__(self, user: User):
        """Initialize task with user."""
        self.user = user
        self.status = TaskStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self._requirements = self.get_requirements()
        self._rewards = self.get_rewards()

    @property
    def duration(self) -> Optional[timedelta]:
        """Get task duration if known."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def time_remaining(self) -> Optional[timedelta]:
        """Get remaining time if task is running."""
        if (self.status == TaskStatus.RUNNING and 
            self.start_time and self.end_time):
            remaining = self.end_time - datetime.now()
            return remaining if remaining.total_seconds() > 0 else timedelta()
        return None

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.COMPLETED

    @property
    def requirements(self) -> TaskRequirements:
        """Get task requirements."""
        return self._requirements

    @property
    def rewards(self) -> TaskRewards:
        """Get task rewards."""
        return self._rewards

    def meets_requirements(self) -> bool:
        """Check if user meets all task requirements."""
        # Check skill requirements
        for skill, level in self.requirements.skills.items():
            if self.user.skill_level(skill) < level:
                return False

        # Check item requirements
        if not self.user.bank.has_all(self.requirements.items):
            return False

        # Check quest requirements
        if not all(quest in self.user.bitfield 
                  for quest in self.requirements.quests):
            return False

        # Check combat level
        if (self.requirements.combat_level and 
            self.user.combat_level < self.requirements.combat_level):
            return False

        # Check GP
        if self.user.GP < self.requirements.gp:
            return False

        return True

    def start(self) -> bool:
        """
        Start the task if requirements are met.
        Returns True if successfully started.
        """
        if not self.meets_requirements():
            return False

        # Remove required items and GP
        if not self.user.bank.remove_all(self.requirements.items):
            return False
            
        self.user.GP -= self.requirements.gp

        self.status = TaskStatus.RUNNING
        self.start_time = datetime.now()
        self.end_time = self.calculate_end_time()

        return True

    def complete(self) -> bool:
        """
        Complete the task and give rewards.
        Returns True if successfully completed.
        """
        if self.status != TaskStatus.RUNNING:
            return False

        # Add reward items and GP
        self.user.bank.add_all(self.rewards.items)
        self.user.GP += self.rewards.gp

        # Add XP rewards
        for skill, xp in self.rewards.xp.items():
            self.user.skills[skill].add_xp(xp)

        self.status = TaskStatus.COMPLETED
        return True

    def cancel(self) -> bool:
        """
        Cancel the task and return required items.
        Returns True if successfully cancelled.
        """
        if self.status != TaskStatus.RUNNING:
            return False

        # Return required items and GP
        self.user.bank.add_all(self.requirements.items)
        self.user.GP += self.requirements.gp

        self.status = TaskStatus.CANCELLED
        return True

    @abstractmethod
    def get_requirements(self) -> TaskRequirements:
        """Get requirements for this task."""
        pass

    @abstractmethod
    def get_rewards(self) -> TaskRewards:
        """Get rewards for this task."""
        pass

    @abstractmethod
    def calculate_end_time(self) -> datetime:
        """Calculate when this task will complete."""
        pass

    @abstractmethod
    def tick(self) -> None:
        """Update task state for this game tick."""
        pass

    def __str__(self) -> str:
        """String representation of task."""
        status_str = f"[{self.status.name}]"
        if self.time_remaining:
            status_str += f" {self.time_remaining}"
        return f"{self.__class__.__name__} {status_str}" 