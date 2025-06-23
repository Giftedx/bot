from typing import Dict, List, Any, Optional
from datetime import datetime

from ...config.achievements import achievement_config, Achievement, AchievementType
from .event_system import EventManager, EventType, GameEvent


class AchievementManager:
    def __init__(self, db_service, event_manager: EventManager):
        self.db_service = db_service
        self.event_manager = event_manager
        self.setup_achievement_listeners()

    def setup_achievement_listeners(self) -> None:
        """Set up listeners for achievement-related events"""
        self.event_manager.subscribe(EventType.PET_OBTAINED, self._check_collection_achievements)
        self.event_manager.subscribe(EventType.PET_LEVELED, self._check_training_achievements)
        self.event_manager.subscribe(EventType.POKEMON_EVOLVED, self._check_evolution_achievements)
        self.event_manager.subscribe(EventType.OSRS_BOSS_KILLED, self._check_boss_achievements)

    async def _check_collection_achievements(self, event: GameEvent) -> None:
        """Check collection-based achievements"""
        user_data = await self._get_user_achievement_data(event.user_id)

        # Update collection data
        pet_type = event.data.get("pet_type")
        pet_name = event.data.get("name", "")
        rarity = event.data.get("rarity", "common")

        if pet_type == "pokemon":
            user_data.setdefault("pokemon_species", []).append(pet_name)
        elif pet_type == "osrs":
            user_data.setdefault("osrs_pets", []).append(pet_name)

        if rarity in ["rare", "epic", "legendary"]:
            user_data["rare_pets"] = user_data.get("rare_pets", 0) + 1

        await self._check_achievements(event.user_id, user_data, AchievementType.COLLECTION)

    async def _check_training_achievements(self, event: GameEvent) -> None:
        """Check training-based achievements"""
        user_data = await self._get_user_achievement_data(event.user_id)

        pet_type = event.data.get("pet_type")
        new_level = event.data.get("level", 0)

        if pet_type == "osrs":
            user_data["osrs_pet_level"] = max(user_data.get("osrs_pet_level", 0), new_level)
            if "combat_level" in event.data:
                user_data["osrs_combat_level"] = max(
                    user_data.get("osrs_combat_level", 0), event.data["combat_level"]
                )
        elif pet_type == "pokemon":
            user_data["pokemon_level"] = max(user_data.get("pokemon_level", 0), new_level)

        await self._check_achievements(event.user_id, user_data, AchievementType.TRAINING)
        await self._check_achievements(event.user_id, user_data, AchievementType.CROSS_SYSTEM)

    async def _check_evolution_achievements(self, event: GameEvent) -> None:
        """Check evolution-based achievements"""
        user_data = await self._get_user_achievement_data(event.user_id)

        user_data["pokemon_evolutions"] = user_data.get("pokemon_evolutions", 0) + 1
        user_data["total_evolutions"] = user_data.get("total_evolutions", 0) + 1

        # Track unique evolutions
        evolved_species = event.data.get("evolved_species", "")
        if evolved_species:
            user_data.setdefault("unique_evolutions", []).append(evolved_species)

        await self._check_achievements(event.user_id, user_data, AchievementType.TRAINING)
        await self._check_achievements(event.user_id, user_data, AchievementType.SPECIAL)

    async def _check_boss_achievements(self, event: GameEvent) -> None:
        """Check boss kill achievements"""
        user_data = await self._get_user_achievement_data(event.user_id)

        kill_count = event.data.get("kill_count", 0)
        user_data["total_boss_kills"] = kill_count

        await self._check_achievements(event.user_id, user_data, AchievementType.SPECIAL)

    async def _get_user_achievement_data(self, user_id: str) -> Dict[str, Any]:
        """Get user's achievement progress data"""
        return await self.db_service.get_user_achievement_data(user_id)

    async def _check_achievements(
        self,
        user_id: str,
        user_data: Dict[str, Any],
        achievement_type: Optional[AchievementType] = None,
    ) -> None:
        """Check if any achievements have been completed"""
        achievements = (
            achievement_config.get_achievements_by_type(achievement_type)
            if achievement_type
            else achievement_config.achievements.values()
        )

        for achievement in achievements:
            # Skip if already completed
            if await self.db_service.has_achievement(user_id, achievement.id):
                continue

            if achievement_config.check_achievement_completion(achievement, user_data):
                await self._grant_achievement(user_id, achievement)

    async def _grant_achievement(self, user_id: str, achievement: Achievement) -> None:
        """Grant an achievement to a user"""
        # Save achievement to database
        await self.db_service.add_achievement(
            user_id,
            {
                "id": achievement.id,
                "name": achievement.name,
                "type": achievement.type.value,
                "awarded_at": datetime.utcnow(),
                "rewards": achievement.rewards,
            },
        )

        # Emit achievement event
        self.event_manager.emit(
            GameEvent(
                type=EventType.ACHIEVEMENT_UNLOCKED,
                user_id=user_id,
                timestamp=datetime.utcnow(),
                data={
                    "achievement": {
                        "id": achievement.id,
                        "name": achievement.name,
                        "type": achievement.type.value,
                        "rewards": achievement.rewards,
                    }
                },
            )
        )

    async def get_user_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all achievements for a user"""
        return await self.db_service.get_user_achievements(user_id)

    async def get_achievement_progress(self, user_id: str) -> Dict[str, Any]:
        """Get progress towards all achievements"""
        user_data = await self._get_user_achievement_data(user_id)
        completed = await self.get_user_achievements(user_id)
        completed_ids = {ach["id"] for ach in completed}

        progress = {}
        for ach in achievement_config.achievements.values():
            if ach.id in completed_ids:
                progress[ach.id] = {"completed": True, "progress": 100, "achievement": ach}
            else:
                # Calculate progress percentage
                total_reqs = len(ach.requirements)
                met_reqs = sum(
                    1
                    for req, value in ach.requirements.items()
                    if req in user_data and user_data[req] >= value
                )
                progress[ach.id] = {
                    "completed": False,
                    "progress": (met_reqs / total_reqs) * 100 if total_reqs > 0 else 0,
                    "achievement": ach,
                }

        return progress
