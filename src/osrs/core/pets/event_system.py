"""Event system for pet-related events and achievements."""
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, List, Callable, Any
from datetime import datetime


class EventType(Enum):
    """Types of pet-related events."""

    PET_CREATED = auto()
    PET_LEVELED = auto()
    PET_TRAINED = auto()
    PET_ABILITY_LEARNED = auto()
    PET_BATTLE_STARTED = auto()
    PET_BATTLE_ENDED = auto()
    PET_BATTLE_MOVE = auto()
    PET_STATUS_APPLIED = auto()
    PET_HEALED = auto()
    PET_DEFEATED = auto()
    BREEDING_STARTED = auto()
    BREEDING_COMPLETED = auto()
    ACHIEVEMENT_UNLOCKED = auto()


@dataclass
class GameEvent:
    """Represents a game event."""

    type: EventType
    user_id: str
    timestamp: datetime
    data: Dict[str, Any]


class EventManager:
    """Manages event handling and dispatching."""

    def __init__(self):
        """Initialize event manager."""
        self.listeners: Dict[EventType, List[Callable[[GameEvent], None]]] = {
            event_type: [] for event_type in EventType
        }
        self._setup_default_listeners()

    def subscribe(self, event_type: EventType, callback: Callable[[GameEvent], None]) -> None:
        """Subscribe to an event type."""
        self.listeners[event_type].append(callback)

    def emit(self, event: GameEvent) -> None:
        """Emit an event to all subscribers."""
        for callback in self.listeners[event.type]:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in event handler: {e}")

    def _setup_default_listeners(self) -> None:
        """Set up default event listeners."""

        def on_pet_leveled(event: GameEvent) -> None:
            """Handle pet level up events."""
            # Check for level-based achievements
            level = event.data["new_level"]
            if level >= 99:
                self.emit(
                    GameEvent(
                        type=EventType.ACHIEVEMENT_UNLOCKED,
                        user_id=event.user_id,
                        timestamp=datetime.utcnow(),
                        data={"achievement_id": "max_level_pet", "pet_id": event.data["pet_id"]},
                    )
                )
            elif level >= 50:
                self.emit(
                    GameEvent(
                        type=EventType.ACHIEVEMENT_UNLOCKED,
                        user_id=event.user_id,
                        timestamp=datetime.utcnow(),
                        data={"achievement_id": "high_level_pet", "pet_id": event.data["pet_id"]},
                    )
                )

        def on_pet_battle_ended(event: GameEvent) -> None:
            """Handle battle completion events."""
            # Check for battle-related achievements
            if event.data.get("win_streak", 0) >= 10:
                self.emit(
                    GameEvent(
                        type=EventType.ACHIEVEMENT_UNLOCKED,
                        user_id=event.user_id,
                        timestamp=datetime.utcnow(),
                        data={"achievement_id": "battle_master", "pet_id": event.data["winner_id"]},
                    )
                )

        def on_breeding_completed(event: GameEvent) -> None:
            """Handle breeding completion events."""
            # Check offspring rarity for achievements
            if event.data["offspring_rarity"] == "mythical":
                self.emit(
                    GameEvent(
                        type=EventType.ACHIEVEMENT_UNLOCKED,
                        user_id=event.user_id,
                        timestamp=datetime.utcnow(),
                        data={
                            "achievement_id": "mythical_breeder",
                            "pet_id": event.data["offspring_id"],
                        },
                    )
                )

        # Register default listeners
        self.subscribe(EventType.PET_LEVELED, on_pet_leveled)
        self.subscribe(EventType.PET_BATTLE_ENDED, on_pet_battle_ended)
        self.subscribe(EventType.BREEDING_COMPLETED, on_breeding_completed)


class AchievementManager:
    """Manages pet-related achievements."""

    def __init__(self, event_manager: EventManager):
        """Initialize achievement manager."""
        self.event_manager = event_manager
        self.achievements: Dict[str, Dict[str, Any]] = {
            "max_level_pet": {
                "name": "Maximum Level",
                "description": "Level a pet to 99",
                "icon": "⭐",
                "reward_xp": 100000,
            },
            "high_level_pet": {
                "name": "High Level",
                "description": "Level a pet to 50",
                "icon": "✨",
                "reward_xp": 50000,
            },
            "battle_master": {
                "name": "Battle Master",
                "description": "Win 10 battles in a row",
                "icon": "⚔️",
                "reward_xp": 75000,
            },
            "mythical_breeder": {
                "name": "Mythical Breeder",
                "description": "Breed a mythical pet",
                "icon": "🥚",
                "reward_xp": 150000,
            },
        }
        self.completed_achievements: Dict[str, List[str]] = {}  # user_id -> achievement_ids
        self.setup_listeners()

    def setup_listeners(self) -> None:
        """Set up achievement event listeners."""

        def on_achievement_unlocked(event: GameEvent) -> None:
            achievement_id = event.data["achievement_id"]
            user_id = event.user_id

            # Check if already completed
            if user_id not in self.completed_achievements:
                self.completed_achievements[user_id] = []
            if achievement_id in self.completed_achievements[user_id]:
                return

            # Mark as completed
            self.completed_achievements[user_id].append(achievement_id)

            # Get achievement data
            achievement = self.achievements[achievement_id]

            # TODO: Grant rewards
            print(f"Achievement unlocked: {achievement['name']} for user {user_id}")
            print(f"Reward: {achievement['reward_xp']} XP")

        self.event_manager.subscribe(EventType.ACHIEVEMENT_UNLOCKED, on_achievement_unlocked)

    def get_user_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all achievements for a user."""
        completed = self.completed_achievements.get(user_id, [])
        return [{**self.achievements[ach_id], "id": ach_id} for ach_id in completed]

    def get_available_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Get achievements that haven't been completed by user."""
        completed = self.completed_achievements.get(user_id, [])
        return [
            {**achievement, "id": ach_id}
            for ach_id, achievement in self.achievements.items()
            if ach_id not in completed
        ]
