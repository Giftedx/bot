"""Quest manager for handling quest progression and requirements."""

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from .game_tick import GameTick, TickPriority
from .skill_manager import SkillType


class QuestDifficulty(Enum):
    """Quest difficulty levels."""

    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    EXPERIENCED = "experienced"
    MASTER = "master"
    GRANDMASTER = "grandmaster"


class QuestStatus(Enum):
    """Quest completion status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class QuestRequirements:
    """Requirements to start a quest."""

    skills: Dict[SkillType, int] = None  # skill: level
    quests: List[str] = None  # quest IDs
    items: Dict[str, int] = None  # item_id: quantity
    combat_level: Optional[int] = None
    quest_points: Optional[int] = None
    is_member: bool = False

    def __post_init__(self):
        """Initialize default values."""
        if self.skills is None:
            self.skills = {}
        if self.quests is None:
            self.quests = []
        if self.items is None:
            self.items = {}


@dataclass
class QuestRewards:
    """Rewards for completing a quest."""

    quest_points: int
    experience: Dict[SkillType, float] = None  # skill: xp
    items: Dict[str, int] = None  # item_id: quantity
    access: List[str] = None  # unlocked content IDs

    def __post_init__(self):
        """Initialize default values."""
        if self.experience is None:
            self.experience = {}
        if self.items is None:
            self.items = {}
        if self.access is None:
            self.access = []


@dataclass
class QuestStep:
    """A step in a quest."""

    id: str
    description: str
    items_required: Dict[str, int] = None  # item_id: quantity
    items_recommended: Dict[str, int] = None  # item_id: quantity
    combat_required: bool = False
    combat_level: Optional[int] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.items_required is None:
            self.items_required = {}
        if self.items_recommended is None:
            self.items_recommended = {}


@dataclass
class Quest:
    """Represents a quest."""

    id: str
    name: str
    difficulty: QuestDifficulty
    requirements: QuestRequirements
    rewards: QuestRewards
    steps: List[QuestStep]
    length: str  # Short/Medium/Long
    series: Optional[str] = None  # Quest series name


class QuestManager:
    """Manages quest progression and requirements."""

    def __init__(self, game_tick: GameTick):
        """Initialize quest manager.

        Args:
            game_tick: GameTick system instance
        """
        self.game_tick = game_tick
        self.quests: Dict[str, Quest] = {}
        self.player_progress: Dict[
            int, Dict[str, QuestStatus]
        ] = {}  # player_id: {quest_id: status}
        self.player_steps: Dict[int, Dict[str, int]] = {}  # player_id: {quest_id: current_step}

        # Register quest tick task
        self.game_tick.register_task("quest_update", self._quest_tick, TickPriority.WORLD)

    async def _quest_tick(self):
        """Process quest updates for current game tick."""
        # Process quest-related events
        pass

    def add_quest(self, quest: Quest):
        """Add a quest to the manager.

        Args:
            quest: Quest to add
        """
        self.quests[quest.id] = quest

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        """Get quest by ID.

        Args:
            quest_id: Quest identifier

        Returns:
            Quest if found, None otherwise
        """
        return self.quests.get(quest_id)

    def get_quest_status(self, player_id: int, quest_id: str) -> QuestStatus:
        """Get player's status for a quest.

        Args:
            player_id: Player's ID
            quest_id: Quest identifier

        Returns:
            Quest status
        """
        return self.player_progress.get(player_id, {}).get(quest_id, QuestStatus.NOT_STARTED)

    def get_current_step(self, player_id: int, quest_id: str) -> Optional[int]:
        """Get player's current step in a quest.

        Args:
            player_id: Player's ID
            quest_id: Quest identifier

        Returns:
            Current step index if in progress
        """
        return self.player_steps.get(player_id, {}).get(quest_id)

    def can_start_quest(
        self,
        player_id: int,
        quest_id: str,
        player_stats: Dict[SkillType, int],
        completed_quests: Set[str],
        quest_points: int,
        inventory: Dict[str, int],
        is_member: bool,
    ) -> Tuple[bool, Optional[str]]:
        """Check if player can start a quest.

        Args:
            player_id: Player's ID
            quest_id: Quest to check
            player_stats: Player's skill levels
            completed_quests: Set of completed quest IDs
            quest_points: Player's quest points
            inventory: Player's inventory
            is_member: Whether player is a member

        Returns:
            Tuple of (can start, reason if cannot)
        """
        quest = self.get_quest(quest_id)
        if not quest:
            return (False, "Quest not found")

        # Check membership
        if quest.requirements.is_member and not is_member:
            return (False, "Members only quest")

        # Check quest points
        if quest.requirements.quest_points and quest_points < quest.requirements.quest_points:
            return (False, f"Requires {quest.requirements.quest_points} quest points")

        # Check combat level
        if (
            quest.requirements.combat_level
            and self._calculate_combat_level(player_stats) < quest.requirements.combat_level
        ):
            return (False, f"Requires combat level {quest.requirements.combat_level}")

        # Check skill requirements
        for skill, level in quest.requirements.skills.items():
            if player_stats.get(skill, 1) < level:
                return (False, f"Requires {skill.value} level {level}")

        # Check quest requirements
        for required_quest in quest.requirements.quests:
            if required_quest not in completed_quests:
                return (False, f"Requires {self.quests[required_quest].name}")

        # Check item requirements
        for item_id, quantity in quest.requirements.items.items():
            if inventory.get(item_id, 0) < quantity:
                return (False, f"Missing required items")

        return (True, None)

    def start_quest(self, player_id: int, quest_id: str) -> bool:
        """Start a quest for a player.

        Args:
            player_id: Player's ID
            quest_id: Quest to start

        Returns:
            True if quest was started
        """
        if quest_id not in self.quests:
            return False

        if player_id not in self.player_progress:
            self.player_progress[player_id] = {}

        current_status = self.get_quest_status(player_id, quest_id)
        if current_status != QuestStatus.NOT_STARTED:
            return False

        self.player_progress[player_id][quest_id] = QuestStatus.IN_PROGRESS
        self.player_steps[player_id] = {quest_id: 0}
        return True

    def advance_quest(self, player_id: int, quest_id: str) -> bool:
        """Advance to next quest step.

        Args:
            player_id: Player's ID
            quest_id: Quest being advanced

        Returns:
            True if quest was advanced
        """
        if quest_id not in self.quests:
            return False

        current_step = self.get_current_step(player_id, quest_id)
        if current_step is None:
            return False

        quest = self.quests[quest_id]
        if current_step >= len(quest.steps) - 1:
            # Complete quest
            self.player_progress[player_id][quest_id] = QuestStatus.COMPLETED
            self.player_steps[player_id].pop(quest_id, None)
        else:
            # Advance to next step
            self.player_steps[player_id][quest_id] = current_step + 1

        return True

    def get_available_quests(
        self,
        player_id: int,
        player_stats: Dict[SkillType, int],
        completed_quests: Set[str],
        quest_points: int,
        inventory: Dict[str, int],
        is_member: bool,
    ) -> List[Quest]:
        """Get quests available to start.

        Args:
            player_id: Player's ID
            player_stats: Player's skill levels
            completed_quests: Set of completed quest IDs
            quest_points: Player's quest points
            inventory: Player's inventory
            is_member: Whether player is a member

        Returns:
            List of available quests
        """
        available = []
        for quest in self.quests.values():
            can_start, _ = self.can_start_quest(
                player_id,
                quest.id,
                player_stats,
                completed_quests,
                quest_points,
                inventory,
                is_member,
            )
            if can_start:
                available.append(quest)

        return available

    def get_quest_series(self, series_name: str) -> List[Quest]:
        """Get all quests in a series.

        Args:
            series_name: Name of quest series

        Returns:
            List of quests in series
        """
        return [quest for quest in self.quests.values() if quest.series == series_name]

    def _calculate_combat_level(self, stats: Dict[SkillType, int]) -> int:
        """Calculate combat level from stats.

        Args:
            stats: Player's skill levels

        Returns:
            Combat level
        """
        base = math.floor(
            (
                stats.get(SkillType.DEFENCE, 1)
                + stats.get(SkillType.HITPOINTS, 10)
                + math.floor(stats.get(SkillType.PRAYER, 1) / 2)
            )
            / 4
        )

        melee = math.floor(
            13 / 40 * (stats.get(SkillType.ATTACK, 1) + stats.get(SkillType.STRENGTH, 1))
        )

        ranged = math.floor(13 / 40 * math.floor(3 * stats.get(SkillType.RANGED, 1) / 2))

        magic = math.floor(13 / 40 * math.floor(3 * stats.get(SkillType.MAGIC, 1) / 2))

        return base + max(melee, ranged, magic)
