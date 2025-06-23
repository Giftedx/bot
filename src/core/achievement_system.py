from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
from dataclasses import dataclass

from ..features.pets.event_system import EventManager, EventType, GameEvent
from .pet_system import Pet, PetOrigin, PetRarity
from .experience import ExperienceManager


class AchievementCategory(Enum):
    COLLECTION = "collection"
    BATTLE = "battle"
    TRAINING = "training"
    INTERACTION = "interaction"
    SPECIAL = "special"
    CROSS_SYSTEM = "cross_system"


@dataclass
class AchievementProgress:
    current_value: int
    target_value: int
    completed: bool = False
    completion_date: Optional[datetime] = None


@dataclass
class Achievement:
    id: str
    name: str
    description: str
    category: AchievementCategory
    target_value: int
    exp_reward: int
    metadata: Dict[str, Any]
    icon: Optional[str] = None
    hidden: bool = False


class AchievementTracker:
    def __init__(self, pet: Pet):
        self.pet = pet
        self.achievements: Dict[str, AchievementProgress] = {}

    def update_progress(self, achievement_id: str, value: int) -> Optional[AchievementProgress]:
        """Update progress for an achievement"""
        if achievement_id not in self.achievements:
            return None

        progress = self.achievements[achievement_id]
        if progress.completed:
            return progress

        progress.current_value = min(value, progress.target_value)
        if progress.current_value >= progress.target_value:
            progress.completed = True
            progress.completion_date = datetime.utcnow()

        return progress


class AchievementManager:
    def __init__(
        self, exp_manager: ExperienceManager, event_manager: Optional[EventManager] = None
    ):
        self.exp_manager = exp_manager
        self.event_manager = event_manager
        self.achievements: Dict[str, Achievement] = {}
        self.pet_trackers: Dict[str, AchievementTracker] = {}  # pet_id -> tracker

        # Initialize default achievements
        self._init_default_achievements()

    def _init_default_achievements(self) -> None:
        """Initialize default achievements"""
        # Collection achievements
        self.register_achievement(
            Achievement(
                id="collect_common_10",
                name="Common Collector",
                description="Collect 10 common pets",
                category=AchievementCategory.COLLECTION,
                target_value=10,
                exp_reward=500,
                metadata={"rarity": PetRarity.COMMON},
            )
        )

        self.register_achievement(
            Achievement(
                id="collect_legendary",
                name="Legendary Discovery",
                description="Obtain your first legendary pet",
                category=AchievementCategory.COLLECTION,
                target_value=1,
                exp_reward=2000,
                metadata={"rarity": PetRarity.LEGENDARY},
            )
        )

        # Battle achievements
        self.register_achievement(
            Achievement(
                id="win_battles_50",
                name="Battle Champion",
                description="Win 50 pet battles",
                category=AchievementCategory.BATTLE,
                target_value=50,
                exp_reward=1000,
                metadata={"type": "wins"},
            )
        )

        self.register_achievement(
            Achievement(
                id="win_ranked_10",
                name="Ranked Warrior",
                description="Win 10 ranked battles",
                category=AchievementCategory.BATTLE,
                target_value=10,
                exp_reward=800,
                metadata={"type": "ranked_wins"},
            )
        )

        # Training achievements
        self.register_achievement(
            Achievement(
                id="reach_level_50",
                name="Master Trainer",
                description="Reach level 50 with any pet",
                category=AchievementCategory.TRAINING,
                target_value=50,
                exp_reward=1500,
                metadata={"type": "level"},
            )
        )

        # Cross-system achievements
        self.register_achievement(
            Achievement(
                id="osrs_beats_pokemon_10",
                name="OSRS Champion",
                description="Win 10 battles against Pokemon with OSRS pets",
                category=AchievementCategory.CROSS_SYSTEM,
                target_value=10,
                exp_reward=1200,
                metadata={"attacker_origin": PetOrigin.OSRS, "defender_origin": PetOrigin.POKEMON},
            )
        )

        self.register_achievement(
            Achievement(
                id="pokemon_beats_osrs_10",
                name="Pokemon Master",
                description="Win 10 battles against OSRS pets with Pokemon",
                category=AchievementCategory.CROSS_SYSTEM,
                target_value=10,
                exp_reward=1200,
                metadata={"attacker_origin": PetOrigin.POKEMON, "defender_origin": PetOrigin.OSRS},
            )
        )

    def register_achievement(self, achievement: Achievement) -> None:
        """Register a new achievement"""
        self.achievements[achievement.id] = achievement

    def get_pet_tracker(self, pet: Pet) -> AchievementTracker:
        """Get or create achievement tracker for a pet"""
        if pet.pet_id not in self.pet_trackers:
            self.pet_trackers[pet.pet_id] = AchievementTracker(pet)
        return self.pet_trackers[pet.pet_id]

    def handle_event(self, event: GameEvent) -> None:
        """Handle game events and update achievements"""
        if not event.user_id or "pet_id" not in event.data:
            return

        pet_id = event.data["pet_id"]
        if pet_id not in self.pet_trackers:
            return

        tracker = self.pet_trackers[pet_id]
        updates: List[Tuple[str, AchievementProgress]] = []

        # Handle different event types
        if event.type == EventType.PET_OBTAINED:
            rarity = event.data.get("rarity")
            if rarity:
                # Update collection achievements
                for achievement in self.achievements.values():
                    if (
                        achievement.category == AchievementCategory.COLLECTION
                        and achievement.metadata.get("rarity") == rarity
                    ):
                        progress = tracker.update_progress(
                            achievement.id, tracker.achievements.get(achievement.id, 0) + 1
                        )
                        if progress:
                            updates.append((achievement.id, progress))

        elif event.type == EventType.BATTLE_COMPLETED:
            if event.data.get("winner_id") == pet_id:
                # Update battle achievements
                battle_type = event.data.get("battle_type")
                for achievement in self.achievements.values():
                    if achievement.category == AchievementCategory.BATTLE:
                        if achievement.metadata["type"] == "wins" or (
                            achievement.metadata["type"] == "ranked_wins"
                            and battle_type == "ranked"
                        ):
                            progress = tracker.update_progress(
                                achievement.id, tracker.achievements.get(achievement.id, 0) + 1
                            )
                            if progress:
                                updates.append((achievement.id, progress))

                # Check cross-system achievements
                if "opponent_origin" in event.data:
                    for achievement in self.achievements.values():
                        if (
                            achievement.category == AchievementCategory.CROSS_SYSTEM
                            and achievement.metadata["attacker_origin"] == tracker.pet.origin
                            and achievement.metadata["defender_origin"].value
                            == event.data["opponent_origin"]
                        ):
                            progress = tracker.update_progress(
                                achievement.id, tracker.achievements.get(achievement.id, 0) + 1
                            )
                            if progress:
                                updates.append((achievement.id, progress))

        elif event.type == EventType.PET_LEVELED:
            new_level = event.data.get("new_level", 0)
            # Update level-based achievements
            for achievement in self.achievements.values():
                if (
                    achievement.category == AchievementCategory.TRAINING
                    and achievement.metadata["type"] == "level"
                ):
                    progress = tracker.update_progress(achievement.id, new_level)
                    if progress:
                        updates.append((achievement.id, progress))

        # Process achievement updates
        for achievement_id, progress in updates:
            achievement = self.achievements[achievement_id]
            if progress.completed:
                # Award experience for completion
                self.exp_manager.award_exp(
                    tracker.pet,
                    achievement.exp_reward,
                    "achievement",
                    {"achievement_id": achievement_id, "achievement_name": achievement.name},
                )

                # Emit achievement completed event
                if self.event_manager:
                    self.event_manager.emit(
                        GameEvent(
                            type=EventType.ACHIEVEMENT_COMPLETED,
                            user_id=event.user_id,
                            timestamp=datetime.utcnow(),
                            data={
                                "pet_id": pet_id,
                                "achievement_id": achievement_id,
                                "achievement_name": achievement.name,
                                "exp_reward": achievement.exp_reward,
                            },
                        )
                    )

    def get_achievements(
        self, pet: Pet, category: Optional[AchievementCategory] = None, include_hidden: bool = False
    ) -> List[Dict[str, Any]]:
        """Get achievements and progress for a pet"""
        tracker = self.get_pet_tracker(pet)
        achievements_data = []

        for achievement in self.achievements.values():
            if achievement.hidden and not include_hidden:
                continue

            if category and achievement.category != category:
                continue

            progress = tracker.achievements.get(
                achievement.id, AchievementProgress(0, achievement.target_value)
            )
            achievements_data.append(
                {
                    "id": achievement.id,
                    "name": achievement.name,
                    "description": achievement.description,
                    "category": achievement.category.value,
                    "progress": progress.current_value,
                    "target": progress.target_value,
                    "completed": progress.completed,
                    "completion_date": progress.completion_date,
                    "exp_reward": achievement.exp_reward,
                    "icon": achievement.icon,
                }
            )

        return achievements_data

    def get_completion_summary(self, pet: Pet) -> Dict[str, Any]:
        """Get achievement completion summary for a pet"""
        tracker = self.get_pet_tracker(pet)
        total = len(self.achievements)
        completed = sum(1 for progress in tracker.achievements.values() if progress.completed)

        by_category = {}
        for category in AchievementCategory:
            category_achievements = [
                a for a in self.achievements.values() if a.category == category
            ]
            completed_in_category = sum(
                1
                for a in category_achievements
                if tracker.achievements.get(a.id, AchievementProgress(0, 1)).completed
            )
            by_category[category.value] = {
                "total": len(category_achievements),
                "completed": completed_in_category,
                "percent": (
                    completed_in_category / len(category_achievements) * 100
                    if category_achievements
                    else 0
                ),
            }

        return {
            "total_achievements": total,
            "total_completed": completed,
            "completion_percent": (completed / total * 100) if total else 0,
            "by_category": by_category,
        }
