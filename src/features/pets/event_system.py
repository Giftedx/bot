from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class EventType(Enum):
    PET_OBTAINED = "pet_obtained"
    PET_LEVELED = "pet_leveled"
    POKEMON_EVOLVED = "pokemon_evolved"
    OSRS_BOSS_KILLED = "osrs_boss_killed"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    SPECIAL_EVENT_TRIGGERED = "special_event_triggered"

@dataclass
class GameEvent:
    type: EventType
    user_id: str
    timestamp: datetime
    data: Dict[str, Any]

class EventManager:
    def __init__(self):
        self.listeners: Dict[EventType, List[Callable[[GameEvent], None]]] = {
            event_type: [] for event_type in EventType
        }
        self._setup_default_listeners()

    def subscribe(self, event_type: EventType, callback: Callable[[GameEvent], None]) -> None:
        """Subscribe to an event type"""
        self.listeners[event_type].append(callback)

    def emit(self, event: GameEvent) -> None:
        """Emit an event to all subscribers"""
        for callback in self.listeners[event.type]:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in event handler: {e}")

    def _setup_default_listeners(self) -> None:
        """Set up default event listeners for cross-system interactions"""
        
        def on_pet_obtained(event: GameEvent) -> None:
            """Handle new pet obtainment"""
            pet_type = event.data.get("pet_type")
            rarity = event.data.get("rarity")
            if rarity == "epic" or rarity == "legendary":
                # Trigger special event for rare pets
                self.emit(GameEvent(
                    type=EventType.SPECIAL_EVENT_TRIGGERED,
                    user_id=event.user_id,
                    timestamp=datetime.utcnow(),
                    data={
                        "trigger": "rare_pet_obtained",
                        "pet_type": pet_type,
                        "rarity": rarity
                    }
                ))

        def on_pokemon_evolved(event: GameEvent) -> None:
            """Handle Pokemon evolution"""
            # Boost OSRS pet chances temporarily
            self.emit(GameEvent(
                type=EventType.SPECIAL_EVENT_TRIGGERED,
                user_id=event.user_id,
                timestamp=datetime.utcnow(),
                data={
                    "trigger": "pokemon_evolution_boost",
                    "duration_hours": 24,
                    "boost_value": 0.15
                }
            ))

        def on_osrs_boss_killed(event: GameEvent) -> None:
            """Handle OSRS boss kills"""
            kill_count = event.data.get("kill_count", 0)
            if kill_count % 100 == 0:  # Every 100 kills
                # Boost Pokemon catch rate temporarily
                self.emit(GameEvent(
                    type=EventType.SPECIAL_EVENT_TRIGGERED,
                    user_id=event.user_id,
                    timestamp=datetime.utcnow(),
                    data={
                        "trigger": "boss_milestone_boost",
                        "duration_hours": 12,
                        "boost_value": 0.1
                    }
                ))

        def on_achievement_unlocked(event: GameEvent) -> None:
            """Handle achievement unlocks"""
            achievement = event.data.get("achievement")
            if achievement.get("type") == "cross_system":
                # Trigger special rewards for cross-system achievements
                self.emit(GameEvent(
                    type=EventType.SPECIAL_EVENT_TRIGGERED,
                    user_id=event.user_id,
                    timestamp=datetime.utcnow(),
                    data={
                        "trigger": "achievement_reward",
                        "achievement": achievement,
                        "rewards": achievement.get("rewards", {})
                    }
                ))

        # Register default listeners
        self.subscribe(EventType.PET_OBTAINED, on_pet_obtained)
        self.subscribe(EventType.POKEMON_EVOLVED, on_pokemon_evolved)
        self.subscribe(EventType.OSRS_BOSS_KILLED, on_osrs_boss_killed)
        self.subscribe(EventType.ACHIEVEMENT_UNLOCKED, on_achievement_unlocked)

class SpecialEventHandler:
    def __init__(self, db_service):
        self.db_service = db_service

    async def handle_special_event(self, event: GameEvent) -> Dict[str, Any]:
        """Handle special events and return relevant data"""
        trigger = event.data.get("trigger")
        
        if trigger == "rare_pet_obtained":
            # Give temporary boosts to all pet types
            boost_data = {
                "osrs": 0.2,
                "pokemon": 0.2,
                "duration_hours": 48
            }
            for pet_type in ["osrs", "pokemon"]:
                self.db_service.set_cross_system_boost(
                    event.user_id,
                    event.data["pet_type"],
                    pet_type,
                    boost_data[pet_type],
                    boost_data["duration_hours"]
                )
            return {"message": "Rare pet bonus activated! All pet catch rates boosted for 48 hours!"}

        elif trigger == "pokemon_evolution_boost":
            # Set evolution-based boost
            self.db_service.set_cross_system_boost(
                event.user_id,
                "pokemon",
                "osrs",
                event.data["boost_value"],
                event.data["duration_hours"]
            )
            return {"message": f"Evolution bonus activated! OSRS pet chances boosted for {event.data['duration_hours']} hours!"}

        elif trigger == "boss_milestone_boost":
            # Set boss milestone boost
            self.db_service.set_cross_system_boost(
                event.user_id,
                "osrs",
                "pokemon",
                event.data["boost_value"],
                event.data["duration_hours"]
            )
            return {"message": f"Boss milestone bonus activated! Pokemon catch rates boosted for {event.data['duration_hours']} hours!"}

        elif trigger == "achievement_reward":
            # Handle achievement rewards
            rewards = event.data.get("rewards", {})
            # Process rewards (could be items, boosts, etc.)
            return {"message": f"Achievement rewards claimed: {rewards}"}

        return {"message": "Unknown special event"} 