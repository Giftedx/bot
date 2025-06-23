"""Unified XP system connecting all game features."""

import logging
from enum import Enum
from typing import Dict, Optional
from datetime import datetime

from src.core.database import DatabaseManager
from src.cache.factory import CacheFactory

logger = logging.getLogger(__name__)


class ActivityType(Enum):
    """Types of activities that can award XP."""

    # OSRS Activities
    OSRS_COMBAT = "osrs_combat"
    OSRS_SKILLING = "osrs_skilling"
    OSRS_QUESTING = "osrs_questing"

    # Pokemon Activities
    POKEMON_BATTLE = "pokemon_battle"
    POKEMON_TRAINING = "pokemon_training"
    POKEMON_BREEDING = "pokemon_breeding"

    # Plex Activities
    PLEX_WATCHING = "plex_watching"
    PLEX_RATING = "plex_rating"
    PLEX_COLLECTING = "plex_collecting"

    # Universal Activities
    ACHIEVEMENT = "achievement"
    EXPLORATION = "exploration"
    COLLECTION = "collection"


class XPSystem:
    """Manages XP across all game systems."""

    def __init__(self, db: DatabaseManager, cache_url: str):
        """Initialize XP system.

        Args:
            db: Database manager instance
            cache_url: Redis cache URL
        """
        self.db = db
        self.cache = CacheFactory.get_redis_cache(cache_url)

    async def award_xp(
        self, player_id: int, activity: ActivityType, amount: float, metadata: Optional[Dict] = None
    ) -> Dict[str, float]:
        """Award XP for an activity with cross-system benefits.

        Args:
            player_id: Player's Discord ID
            activity: Type of activity
            amount: Base XP amount
            metadata: Additional activity data

        Returns:
            Dictionary of XP awarded to different systems
        """
        try:
            # Calculate cross-system benefits
            xp_awards = self._calculate_xp_distribution(activity, amount)

            # Cache recent XP gains
            cache_key = f"recent_xp:{player_id}"
            recent_xp = self.cache.get(cache_key) or {}
            recent_xp[activity.value] = {
                "amount": amount,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata,
            }
            self.cache.set(cache_key, recent_xp)

            # Update database
            async with self.db.get_session() as session:
                # Update specific system XP
                if activity.value.startswith("osrs_"):
                    await self._update_osrs_xp(session, player_id, xp_awards)
                elif activity.value.startswith("pokemon_"):
                    await self._update_pokemon_xp(session, player_id, xp_awards)
                elif activity.value.startswith("plex_"):
                    await self._update_plex_xp(session, player_id, xp_awards)

                # Update universal XP
                await self._update_universal_xp(session, player_id, xp_awards)

            return xp_awards

        except Exception as e:
            logger.error(f"Error awarding XP: {e}")
            return {}

    def _calculate_xp_distribution(
        self, activity: ActivityType, base_amount: float
    ) -> Dict[str, float]:
        """Calculate how XP should be distributed across systems.

        Args:
            activity: Type of activity
            base_amount: Base XP amount

        Returns:
            Dictionary of XP amounts per system
        """
        awards = {
            "primary": base_amount,  # Full amount to primary system
            "universal": base_amount * 0.1,  # 10% to universal progress
        }

        # Cross-system benefits
        if activity in [ActivityType.OSRS_COMBAT, ActivityType.POKEMON_BATTLE]:
            awards["combat_mastery"] = base_amount * 0.05

        if activity in [ActivityType.OSRS_SKILLING, ActivityType.POKEMON_TRAINING]:
            awards["skill_mastery"] = base_amount * 0.05

        if activity in [ActivityType.COLLECTION, ActivityType.EXPLORATION]:
            awards["discovery_mastery"] = base_amount * 0.05

        return awards

    async def _update_osrs_xp(self, session, player_id: int, awards: Dict[str, float]) -> None:
        """Update OSRS-specific XP awards."""
        # Implementation depends on OSRS database schema
        pass

    async def _update_pokemon_xp(self, session, player_id: int, awards: Dict[str, float]) -> None:
        """Update Pokemon-specific XP awards."""
        # Implementation depends on Pokemon database schema
        pass

    async def _update_plex_xp(self, session, player_id: int, awards: Dict[str, float]) -> None:
        """Update Plex-specific XP awards."""
        # Implementation depends on Plex database schema
        pass

    async def _update_universal_xp(self, session, player_id: int, awards: Dict[str, float]) -> None:
        """Update universal XP and level progress."""
        # Implementation depends on core database schema
        pass
