"""Experience manager for handling experience and level calculations."""

from typing import Dict, Optional, Tuple
from .data_manager import DataManager


class ExperienceManager(DataManager):
    """Manages experience and level calculations."""

    def __init__(self, data_dir: str = "src/osrs/data"):
        """Initialize the experience manager.

        Args:
            data_dir: Directory containing data files.
        """
        super().__init__(data_dir)
        self.XP_FILE = "experience_tables.json"

    def get_level_for_xp(self, xp: float) -> int:
        """Get the level for a given amount of experience.

        Args:
            xp: The amount of experience.

        Returns:
            The corresponding level.
        """
        level_xp = self.get_data(self.XP_FILE, "level_experience")

        for level in range(99, 0, -1):
            if xp >= float(level_xp[str(level)]):
                return level
        return 1

    def get_xp_for_level(self, level: int) -> float:
        """Get the minimum experience required for a level.

        Args:
            level: The target level.

        Returns:
            The required experience.

        Raises:
            ValueError: If level is not between 1 and 99.
        """
        if not 1 <= level <= 99:
            raise ValueError("Level must be between 1 and 99")

        level_xp = self.get_data(self.XP_FILE, "level_experience")
        return float(level_xp[str(level)])

    def get_xp_to_next_level(self, current_xp: float) -> Tuple[float, int]:
        """Calculate experience needed for next level.

        Args:
            current_xp: Current experience amount.

        Returns:
            Tuple of (xp_needed, next_level).
        """
        current_level = self.get_level_for_xp(current_xp)
        if current_level >= 99:
            return (0, 99)

        next_level = current_level + 1
        needed_xp = self.get_xp_for_level(next_level) - current_xp

        return (needed_xp, next_level)

    def get_combat_xp(self, monster_id: str) -> Dict[str, float]:
        """Get combat experience for killing a monster.

        Args:
            monster_id: The ID of the monster.

        Returns:
            Dict of experience values by skill.
        """
        combat_xp = self.get_data(self.XP_FILE, "combat_experience")
        monster_data = combat_xp.get(monster_id, {})

        if not monster_data:
            return {}

        base_xp = monster_data["base_experience"]
        hp_xp = monster_data["hitpoints"] * monster_data["hitpoint_experience"]

        return {
            "hitpoints": hp_xp,
            "attack": base_xp,
            "strength": base_xp,
            "defence": base_xp,
            "ranged": base_xp,
            "magic": base_xp,
        }

    def get_skilling_xp(self, skill: str, action: str) -> Optional[float]:
        """Get experience for a skilling action.

        Args:
            skill: The skill being trained.
            action: The training action.

        Returns:
            The experience amount or None if not found.
        """
        skilling_xp = self.get_data(self.XP_FILE, "skilling_experience")

        if skill in skilling_xp and action in skilling_xp[skill]:
            return skilling_xp[skill][action]["experience"]
        return None

    def get_skill_requirement(self, skill: str, action: str) -> Optional[int]:
        """Get level requirement for a skilling action.

        Args:
            skill: The skill being trained.
            action: The training action.

        Returns:
            The required level or None if not found.
        """
        skilling_xp = self.get_data(self.XP_FILE, "skilling_experience")

        if skill in skilling_xp and action in skilling_xp[skill]:
            return skilling_xp[skill][action]["level"]
        return None
