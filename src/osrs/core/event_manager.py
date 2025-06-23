"""OSRS event manager."""
from typing import Callable, Dict, List, Optional, Set, Tuple, Union
from datetime import datetime
import logging
from enum import Enum, auto

from .game_state import GameState
from .world_manager import WorldManager
from .map.WorldMap import WorldPoint
from ..database.models import Database

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of game events."""

    SKILL_LEVEL_UP = auto()
    QUEST_COMPLETE = auto()
    ACHIEVEMENT_COMPLETE = auto()
    COMBAT_VICTORY = auto()
    COMBAT_DEATH = auto()
    ITEM_ACQUIRED = auto()
    LOCATION_REACHED = auto()
    MINIGAME_COMPLETE = auto()
    TITLE_UNLOCKED = auto()
    RELATIONSHIP_FORMED = auto()
    BOOST_APPLIED = auto()
    BOOST_EXPIRED = auto()


class GameEvent:
    """Represents a game event."""

    def __init__(
        self,
        event_type: EventType,
        player_id: int,
        data: Dict,
        timestamp: Optional[datetime] = None,
    ):
        """Initialize game event."""
        self.event_type = event_type
        self.player_id = player_id
        self.data = data
        self.timestamp = timestamp or datetime.utcnow()


class EventManager:
    """Manages game events and their handlers."""

    def __init__(self, database: Database, game_state: GameState, world_manager: WorldManager):
        """Initialize event manager."""
        self.db = database
        self.game_state = game_state
        self.world_manager = world_manager
        self.event_handlers: Dict[EventType, List[Callable]] = {
            event_type: [] for event_type in EventType
        }
        self.pending_events: List[GameEvent] = []
        self.register_default_handlers()

    def register_handler(self, event_type: EventType, handler: Callable) -> None:
        """Register an event handler."""
        self.event_handlers[event_type].append(handler)

    def register_default_handlers(self) -> None:
        """Register default event handlers."""
        # Skill level up handlers
        self.register_handler(EventType.SKILL_LEVEL_UP, self._handle_skill_level_up)

        # Quest completion handlers
        self.register_handler(EventType.QUEST_COMPLETE, self._handle_quest_complete)

        # Achievement handlers
        self.register_handler(EventType.ACHIEVEMENT_COMPLETE, self._handle_achievement_complete)

        # Combat handlers
        self.register_handler(EventType.COMBAT_VICTORY, self._handle_combat_victory)
        self.register_handler(EventType.COMBAT_DEATH, self._handle_combat_death)

        # Item handlers
        self.register_handler(EventType.ITEM_ACQUIRED, self._handle_item_acquired)

        # Location handlers
        self.register_handler(EventType.LOCATION_REACHED, self._handle_location_reached)

        # Minigame handlers
        self.register_handler(EventType.MINIGAME_COMPLETE, self._handle_minigame_complete)

        # Title handlers
        self.register_handler(EventType.TITLE_UNLOCKED, self._handle_title_unlocked)

        # Relationship handlers
        self.register_handler(EventType.RELATIONSHIP_FORMED, self._handle_relationship_formed)

        # Boost handlers
        self.register_handler(EventType.BOOST_APPLIED, self._handle_boost_applied)
        self.register_handler(EventType.BOOST_EXPIRED, self._handle_boost_expired)

    def dispatch_event(self, event: GameEvent) -> None:
        """Dispatch an event to its handlers."""
        logger.info(f"Dispatching event {event.event_type} for player {event.player_id}")

        for handler in self.event_handlers[event.event_type]:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event.event_type}: {str(e)}")

        self.pending_events.append(event)

    def process_pending_events(self) -> None:
        """Process any pending events."""
        while self.pending_events:
            event = self.pending_events.pop(0)
            self._record_event(event)

    def _record_event(self, event: GameEvent) -> None:
        """Record an event in the database."""
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                INSERT INTO game_events (
                    player_id, event_type, event_data, timestamp
                ) VALUES (?, ?, ?, ?)
                """,
                (event.player_id, event.event_type.name, str(event.data), event.timestamp),
            )

    def _handle_skill_level_up(self, event: GameEvent) -> None:
        """Handle skill level up events."""
        skill_name = event.data["skill_name"]
        new_level = event.data["new_level"]

        # Update player skills
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                UPDATE skills
                SET level = ?
                WHERE player_id = ? AND skill_type = ?
                """,
                (new_level, event.player_id, skill_name),
            )

        # Check for total level milestones
        cursor.execute(
            """
            SELECT SUM(level) as total_level
            FROM skills
            WHERE player_id = ?
            """,
            (event.player_id,),
        )
        total_level = cursor.fetchone()["total_level"]

        # Handle milestones (500, 1000, 1500, 2000)
        if total_level in (500, 1000, 1500, 2000):
            self.dispatch_event(
                GameEvent(
                    EventType.TITLE_UNLOCKED,
                    event.player_id,
                    {"title": f"Level {total_level}", "make_active": True},
                )
            )

    def _handle_quest_complete(self, event: GameEvent) -> None:
        """Handle quest completion events."""
        quest_id = event.data["quest_id"]

        # Update quest progress
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                UPDATE quest_progress
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE player_id = ? AND quest_id = ?
                """,
                (event.player_id, quest_id),
            )

        # Check quest point milestones
        cursor.execute(
            """
            SELECT COUNT(*) as quest_points
            FROM quest_progress
            WHERE player_id = ? AND status = 'completed'
            """,
            (event.player_id,),
        )
        quest_points = cursor.fetchone()["quest_points"]

        # Handle milestones
        if quest_points in (50, 100, 150, 200):
            self.dispatch_event(
                GameEvent(
                    EventType.TITLE_UNLOCKED,
                    event.player_id,
                    {"title": f"Quester {quest_points}", "make_active": True},
                )
            )

    def _handle_achievement_complete(self, event: GameEvent) -> None:
        """Handle achievement completion events."""
        diary_id = event.data["diary_id"]
        task_id = event.data["task_id"]

        # Update achievement progress
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                INSERT INTO achievement_progress (
                    player_id, diary_id, task_id, completed_at
                ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (event.player_id, diary_id, task_id),
            )

        # Check for diary completion
        cursor.execute(
            """
            SELECT COUNT(*) as completed_tasks
            FROM achievement_progress
            WHERE player_id = ? AND diary_id = ?
            """,
            (event.player_id, diary_id),
        )
        completed_tasks = cursor.fetchone()["completed_tasks"]

        # If diary is complete, award title
        if completed_tasks >= event.data.get("total_tasks", 0):
            self.dispatch_event(
                GameEvent(
                    EventType.TITLE_UNLOCKED,
                    event.player_id,
                    {"title": f"{diary_id} Master", "make_active": True},
                )
            )

    def _handle_combat_victory(self, event: GameEvent) -> None:
        """Handle combat victory events."""
        self.game_state.record_combat_stats(
            event.player_id, kills=1, damage_dealt=event.data.get("damage_dealt", 0)
        )

    def _handle_combat_death(self, event: GameEvent) -> None:
        """Handle combat death events."""
        self.game_state.record_combat_stats(
            event.player_id, deaths=1, damage_taken=event.data.get("damage_taken", 0)
        )

    def _handle_item_acquired(self, event: GameEvent) -> None:
        """Handle item acquisition events."""
        item_id = event.data["item_id"]
        quantity = event.data.get("quantity", 1)

        # Update collection log if applicable
        if event.data.get("add_to_collection", False):
            self.game_state.update_collection_log(
                event.player_id, event.data.get("category", "Miscellaneous"), item_id, quantity
            )

    def _handle_location_reached(self, event: GameEvent) -> None:
        """Handle location reached events."""
        location = WorldPoint(event.data["x"], event.data["y"], event.data.get("plane", 0))

        # Update player location
        self.game_state.update_player_location(event.player_id, location)

    def _handle_minigame_complete(self, event: GameEvent) -> None:
        """Handle minigame completion events."""
        self.game_state.update_minigame_score(
            event.player_id, event.data["minigame"], event.data["score"]
        )

    def _handle_title_unlocked(self, event: GameEvent) -> None:
        """Handle title unlock events."""
        self.game_state.add_player_title(
            event.player_id, event.data["title"], event.data.get("make_active", False)
        )

    def _handle_relationship_formed(self, event: GameEvent) -> None:
        """Handle relationship formation events."""
        self.game_state.add_relationship(
            event.player_id, event.data["related_player_id"], event.data["relationship_type"]
        )

    def _handle_boost_applied(self, event: GameEvent) -> None:
        """Handle boost application events."""
        self.game_state.add_cross_system_boost(
            event.player_id,
            event.data["source_type"],
            event.data["target_type"],
            event.data["boost_value"],
            event.data.get("duration_seconds"),
        )

    def _handle_boost_expired(self, event: GameEvent) -> None:
        """Handle boost expiration events."""
        # Remove expired boost
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                DELETE FROM cross_system_boosts
                WHERE player_id = ?
                  AND source_type = ?
                  AND target_type = ?
                """,
                (event.player_id, event.data["source_type"], event.data["target_type"]),
            )
