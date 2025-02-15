"""Woodcutting skill implementation."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Dict, Optional, Set

from .base_skill_task import BaseSkillTask
from ..task import TaskRequirements, TaskRewards
from ..skills import SkillType
from ...models.user import User


class TreeType(Enum):
    """Types of trees that can be cut."""
    REGULAR = auto()
    OAK = auto()
    WILLOW = auto()
    MAPLE = auto()
    YEW = auto()
    MAGIC = auto()
    REDWOOD = auto()


@dataclass
class TreeData:
    """Data for each tree type."""
    level: int
    xp: float
    log_id: str
    respawn_ticks: int
    base_success_chance: float
    min_axe_tier: int


TREE_DATA: Dict[TreeType, TreeData] = {
    TreeType.REGULAR: TreeData(
        level=1,
        xp=25.0,
        log_id="logs",
        respawn_ticks=4,
        base_success_chance=0.5,
        min_axe_tier=1
    ),
    TreeType.OAK: TreeData(
        level=15,
        xp=37.5,
        log_id="oak_logs",
        respawn_ticks=7,
        base_success_chance=0.45,
        min_axe_tier=1
    ),
    TreeType.WILLOW: TreeData(
        level=30,
        xp=67.5,
        log_id="willow_logs",
        respawn_ticks=7,
        base_success_chance=0.4,
        min_axe_tier=1
    ),
    TreeType.MAPLE: TreeData(
        level=45,
        xp=100.0,
        log_id="maple_logs",
        respawn_ticks=9,
        base_success_chance=0.35,
        min_axe_tier=2
    ),
    TreeType.YEW: TreeData(
        level=60,
        xp=175.0,
        log_id="yew_logs",
        respawn_ticks=10,
        base_success_chance=0.3,
        min_axe_tier=3
    ),
    TreeType.MAGIC: TreeData(
        level=75,
        xp=250.0,
        log_id="magic_logs",
        respawn_ticks=12,
        base_success_chance=0.25,
        min_axe_tier=4
    ),
    TreeType.REDWOOD: TreeData(
        level=90,
        xp=380.0,
        log_id="redwood_logs",
        respawn_ticks=15,
        base_success_chance=0.2,
        min_axe_tier=5
    )
}


class WoodcuttingTask(BaseSkillTask):
    """Task for cutting trees."""

    def __init__(self, user: User, tree_type: TreeType, duration: timedelta):
        """Initialize woodcutting task."""
        super().__init__(user, SkillType.WOODCUTTING)
        self.tree_type = tree_type
        self.tree_data = TREE_DATA[tree_type]
        self._duration = duration
        self.ticks_per_action = self.get_base_ticks_per_action()

    def get_requirements(self) -> TaskRequirements:
        """Get requirements for woodcutting."""
        return TaskRequirements(
            skills={SkillType.WOODCUTTING: self.tree_data.level}
        )

    def get_rewards(self) -> TaskRewards:
        """Get estimated rewards for woodcutting session."""
        # Estimate number of successful actions
        ticks = self._duration.total_seconds() / 0.6  # 0.6s per tick
        actions = ticks / self.ticks_per_action
        success_rate = self.calculate_success_chance()
        successful_actions = int(actions * success_rate)

        return TaskRewards(
            xp={
                SkillType.WOODCUTTING: 
                int(successful_actions * self.tree_data.xp)
            },
            items={
                self.tree_data.log_id: successful_actions
            }
        )

    def calculate_end_time(self) -> datetime:
        """Calculate when woodcutting session will end."""
        return datetime.now() + self._duration

    def calculate_success_chance(self) -> float:
        """Calculate chance of successfully cutting the tree."""
        level = self.user.skill_level(SkillType.WOODCUTTING)
        level_factor = (level - self.tree_data.level) / 99.0
        
        # TODO: Factor in axe type when equipment system is implemented
        axe_bonus = 0.1  # Assume bronze axe for now
        
        base = self.tree_data.base_success_chance
        return min(0.9, base + level_factor + axe_bonus)

    def calculate_xp_per_action(self) -> float:
        """Calculate XP gained per successful cut."""
        return self.tree_data.xp

    def get_base_ticks_per_action(self) -> int:
        """Get base number of game ticks per woodcutting attempt."""
        return self.tree_data.respawn_ticks

    def __str__(self) -> str:
        """String representation of woodcutting task."""
        base = super().__str__()
        return f"{base} - {self.tree_type.name} Tree" 