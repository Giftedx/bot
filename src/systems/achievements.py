"""Universal achievement system tracking progress across all games."""

import logging
from enum import Enum
from typing import Dict, List, Any
from datetime import datetime

from src.core.database import DatabaseManager
from src.cache.factory import CacheFactory
from .unified_xp import XPSystem, ActivityType
from .resource_system import ResourceSystem

logger = logging.getLogger(__name__)


class AchievementCategory(Enum):
    """Categories of achievements."""

    # Game-Specific
    OSRS_COMBAT = "osrs_combat"
    OSRS_SKILLS = "osrs_skills"
    OSRS_QUESTS = "osrs_quests"

    POKEMON_TRAINING = "pokemon_training"
    POKEMON_COLLECTION = "pokemon_collection"
    POKEMON_BATTLE = "pokemon_battle"

    PLEX_WATCHING = "plex_watching"
    PLEX_COLLECTION = "plex_collection"
    PLEX_RATING = "plex_rating"

    # Cross-Game
    UNIVERSAL_MASTERY = "universal_mastery"
    RESOURCE_COLLECTION = "resource_collection"
    MILESTONE = "milestone"


class Achievement:
    """Represents a completable achievement."""

    def __init__(
        self,
        id: str,
        category: AchievementCategory,
        name: str,
        description: str,
        requirements: Dict[str, Any],
        rewards: Dict[str, Any],
        points: int = 1,
    ):
        """Initialize achievement.

        Args:
            id: Unique achievement ID
            category: Achievement category
            name: Display name
            description: Achievement description
            requirements: Completion requirements
            rewards: Rewards for completion
            points: Achievement points value
        """
        self.id = id
        self.category = category
        self.name = name
        self.description = description
        self.requirements = requirements
        self.rewards = rewards
        self.points = points


class AchievementSystem:
    """Manages achievements and progress tracking."""

    def __init__(
        self,
        db: DatabaseManager,
        cache_url: str,
        xp_system: XPSystem,
        resource_system: ResourceSystem,
    ):
        """Initialize achievement system.

        Args:
            db: Database manager instance
            cache_url: Redis cache URL
            xp_system: XP system instance
            resource_system: Resource system instance
        """
        self.db = db
        self.cache = CacheFactory.get_redis_cache(cache_url)
        self.xp_system = xp_system
        self.resource_system = resource_system

        # Initialize achievements
        self.achievements = self._initialize_achievements()

    def _initialize_achievements(self) -> Dict[str, Achievement]:
        """Initialize all achievements."""
        achievements = {}

        # OSRS Achievements
        achievements["osrs_combat_master"] = Achievement(
            "osrs_combat_master",
            AchievementCategory.OSRS_COMBAT,
            "Combat Master",
            "Reach level 99 in all combat skills",
            {"skills": {"attack": 99, "strength": 99, "defence": 99}},
            {"xp_boost": 1.1, "title": "the Combat Master"},
            10,
        )

        # Pokemon Achievements
        achievements["pokemon_collector"] = Achievement(
            "pokemon_collector",
            AchievementCategory.POKEMON_COLLECTION,
            "Pokemon Collector",
            "Catch 100 unique Pokemon",
            {"unique_pokemon": 100},
            {"rare_candy": 5, "master_ball": 1},
            5,
        )

        # Cross-Game Achievements
        achievements["resource_baron"] = Achievement(
            "resource_baron",
            AchievementCategory.RESOURCE_COLLECTION,
            "Resource Baron",
            "Collect 1000 total resources across all games",
            {"total_resources": 1000},
            {"universal_multiplier": 1.05, "title": "the Resource Baron"},
            15,
        )

        return achievements

    async def check_achievement(
        self, player_id: int, category: AchievementCategory, progress_update: Dict[str, Any]
    ) -> List[Achievement]:
        """Check for completed achievements.

        Args:
            player_id: Player's Discord ID
            category: Category to check
            progress_update: New progress data

        Returns:
            List of newly completed achievements
        """
        try:
            completed = []

            # Get current progress
            async with self.db.get_session() as session:
                current_progress = await self._get_progress(session, player_id)

            # Update progress
            self._update_progress(current_progress, category, progress_update)

            # Check achievements in category
            for achievement in self.achievements.values():
                if achievement.category == category:
                    if self._check_requirements(achievement, current_progress):
                        if not await self._is_completed(player_id, achievement.id):
                            completed.append(achievement)
                            await self._award_achievement(player_id, achievement)

            return completed

        except Exception as e:
            logger.error(f"Error checking achievements: {e}")
            return []

    def _check_requirements(self, achievement: Achievement, progress: Dict[str, Any]) -> bool:
        """Check if achievement requirements are met.

        Args:
            achievement: Achievement to check
            progress: Current progress data

        Returns:
            True if requirements met, False otherwise
        """
        try:
            for key, required in achievement.requirements.items():
                if isinstance(required, dict):
                    # Nested requirements (e.g., skills)
                    current = progress.get(key, {})
                    if not all(current.get(k, 0) >= v for k, v in required.items()):
                        return False
                else:
                    # Simple numeric requirement
                    if progress.get(key, 0) < required:
                        return False
            return True

        except Exception as e:
            logger.error(f"Error checking requirements: {e}")
            return False

    async def _award_achievement(self, player_id: int, achievement: Achievement) -> None:
        """Award achievement rewards to player.

        Args:
            player_id: Player's Discord ID
            achievement: Completed achievement
        """
        try:
            # Award XP
            await self.xp_system.award_xp(
                player_id,
                ActivityType.ACHIEVEMENT,
                100.0 * achievement.points,
                {"achievement_id": achievement.id},
            )

            # Save completion
            async with self.db.get_session() as session:
                await self._save_completion(session, player_id, achievement)

            # Cache recent achievements
            cache_key = f"recent_achievements:{player_id}"
            recent = self.cache.get(cache_key) or []
            recent.append(
                {
                    "id": achievement.id,
                    "name": achievement.name,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            self.cache.set(cache_key, recent[-10:])  # Keep last 10

        except Exception as e:
            logger.error(f"Error awarding achievement: {e}")

    async def _get_progress(self, session, player_id: int) -> Dict[str, Any]:
        """Get current achievement progress."""
        # Implementation depends on database schema
        pass

    async def _is_completed(self, player_id: int, achievement_id: str) -> bool:
        """Check if achievement already completed."""
        # Implementation depends on database schema
        pass

    async def _save_completion(self, session, player_id: int, achievement: Achievement) -> None:
        """Save achievement completion."""
        # Implementation depends on database schema
        pass

    def _update_progress(
        self, current: Dict[str, Any], category: AchievementCategory, update: Dict[str, Any]
    ) -> None:
        """Update progress with new data."""
        # Implementation depends on progress structure
        pass
