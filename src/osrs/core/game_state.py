"""OSRS game state manager."""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

from ..database.models import Database
from ..core.map.WorldMap import WorldPoint
from ..core.map.map_utils import (
    calculate_distance,
    find_nearest_transport,
    find_teleport_to_destination,
    get_path_between_points,
    is_in_members_area
)

logger = logging.getLogger(__name__)

class GameState:
    """Manages the game state and core logic."""
    
    def __init__(self, database: Database):
        """Initialize game state manager."""
        self.db = database
        self.active_players: Dict[int, Dict] = {}  # discord_id -> player_data
        self.current_locations: Dict[int, WorldPoint] = {}  # player_id -> location
        
    def load_player(self, discord_id: int) -> Optional[Dict]:
        """Load player data from database."""
        player_data = self.db.get_player(discord_id)
        if player_data:
            self.active_players[discord_id] = player_data
            # Set default location if not set
            if player_data['id'] not in self.current_locations:
                self.current_locations[player_data['id']] = WorldPoint(3222, 3218, 0)  # Lumbridge
        return player_data
        
    def update_player_location(self, player_id: int, new_location: WorldPoint) -> bool:
        """Update player's current location."""
        if player_id not in self.current_locations:
            return False
            
        old_location = self.current_locations[player_id]
        distance = calculate_distance(old_location, new_location)
        
        # Validate movement
        if distance > 50:  # Max allowed distance without teleport
            logger.warning(f"Player {player_id} attempted to move too far: {distance} tiles")
            return False
            
        self.current_locations[player_id] = new_location
        return True
        
    def start_training_session(
        self,
        player_id: int,
        skill_name: str,
        location: WorldPoint
    ) -> Optional[int]:
        """Start a new training session."""
        player = next(
            (p for p in self.active_players.values() if p['id'] == player_id),
            None
        )
        if not player:
            return None
            
        current_level = player['skills'].get(skill_name, 1)
        
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                INSERT INTO training_sessions (
                    player_id, skill_name, start_time, start_level,
                    location_x, location_y, plane
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (
                    player_id, skill_name, datetime.utcnow(),
                    current_level, location.x, location.y, location.plane
                )
            )
            session_id = cursor.fetchone()[0]
            
        return session_id
        
    def end_training_session(
        self,
        session_id: int,
        xp_gained: int
    ) -> bool:
        """End a training session and record results."""
        with self.db.conn:
            cursor = self.db.conn.cursor()
            
            # Get session data
            cursor.execute(
                "SELECT * FROM training_sessions WHERE id = ?",
                (session_id,)
            )
            session = cursor.fetchone()
            if not session:
                return False
                
            # Get current skill level
            cursor.execute(
                """
                SELECT xp FROM skills 
                WHERE player_id = ? AND skill_type = ?
                """,
                (session['player_id'], session['skill_name'])
            )
            current_xp = cursor.fetchone()[0]
            
            # Calculate new level
            new_level = self._calculate_level(current_xp + xp_gained)
            
            # Update session
            cursor.execute(
                """
                UPDATE training_sessions
                SET end_time = ?, end_level = ?, xp_gained = ?
                WHERE id = ?
                """,
                (
                    datetime.utcnow(),
                    new_level,
                    xp_gained,
                    session_id
                )
            )
            
            # Update player skills
            cursor.execute(
                """
                UPDATE skills
                SET xp = xp + ?, level = ?
                WHERE player_id = ? AND skill_type = ?
                """,
                (
                    xp_gained,
                    new_level,
                    session['player_id'],
                    session['skill_name']
                )
            )
            
        return True
        
    def record_combat_stats(
        self,
        player_id: int,
        kills: int = 0,
        deaths: int = 0,
        damage_dealt: int = 0,
        damage_taken: int = 0
    ) -> None:
        """Record combat statistics."""
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                INSERT INTO combat_stats (
                    player_id, kills, deaths,
                    damage_dealt, damage_taken
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (player_id) DO UPDATE SET
                    kills = combat_stats.kills + ?,
                    deaths = combat_stats.deaths + ?,
                    damage_dealt = combat_stats.damage_dealt + ?,
                    damage_taken = combat_stats.damage_taken + ?,
                    last_updated = CURRENT_TIMESTAMP
                """,
                (
                    player_id, kills, deaths, damage_dealt, damage_taken,
                    kills, deaths, damage_dealt, damage_taken
                )
            )
            
    def record_transaction(
        self,
        player_id: int,
        item_id: str,
        quantity: int,
        price_per_item: int,
        transaction_type: str
    ) -> None:
        """Record a player transaction."""
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                INSERT INTO transactions (
                    player_id, item_id, quantity,
                    price_per_item, transaction_type
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    player_id, item_id, quantity,
                    price_per_item, transaction_type
                )
            )
            
    def update_collection_log(
        self,
        player_id: int,
        category: str,
        item_id: str,
        count: int = 1
    ) -> None:
        """Update player's collection log."""
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                INSERT INTO collection_log (
                    player_id, category, item_id,
                    count, first_obtained, last_obtained
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (player_id, category, item_id) DO UPDATE SET
                    count = collection_log.count + ?,
                    last_obtained = CURRENT_TIMESTAMP
                """,
                (player_id, category, item_id, count, count)
            )
            
    def update_minigame_score(
        self,
        player_id: int,
        minigame: str,
        score: int
    ) -> None:
        """Update player's minigame score."""
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                INSERT INTO minigame_scores (
                    player_id, minigame, score, high_score
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT (player_id, minigame) DO UPDATE SET
                    score = ?,
                    high_score = CASE 
                        WHEN ? > minigame_scores.high_score 
                        THEN ? 
                        ELSE minigame_scores.high_score 
                    END,
                    last_played = CURRENT_TIMESTAMP
                """,
                (
                    player_id, minigame, score, score,
                    score, score, score
                )
            )
            
    def add_player_title(
        self,
        player_id: int,
        title: str,
        make_active: bool = False
    ) -> None:
        """Add a title to player's collection."""
        with self.db.conn:
            cursor = self.db.conn.cursor()
            
            # Add new title
            cursor.execute(
                """
                INSERT INTO player_titles (
                    player_id, title, is_active
                ) VALUES (?, ?, ?)
                ON CONFLICT (player_id, title) DO UPDATE SET
                    is_active = ?
                """,
                (player_id, title, make_active, make_active)
            )
            
            # If making active, deactivate other titles
            if make_active:
                cursor.execute(
                    """
                    UPDATE player_titles
                    SET is_active = FALSE
                    WHERE player_id = ?
                      AND title != ?
                    """,
                    (player_id, title)
                )
                
    def add_relationship(
        self,
        player_id: int,
        related_player_id: int,
        relationship_type: str
    ) -> None:
        """Add a relationship between players."""
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                INSERT INTO player_relationships (
                    player_id, related_player_id, relationship_type
                ) VALUES (?, ?, ?)
                ON CONFLICT (player_id, related_player_id, relationship_type)
                DO NOTHING
                """,
                (player_id, related_player_id, relationship_type)
            )
            
    def add_cross_system_boost(
        self,
        player_id: int,
        source_type: str,
        target_type: str,
        boost_value: float,
        duration_seconds: Optional[int] = None
    ) -> None:
        """Add a cross-system boost."""
        expires_at = (
            datetime.utcnow().timestamp() + duration_seconds
            if duration_seconds
            else None
        )
        
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute(
                """
                INSERT INTO cross_system_boosts (
                    player_id, source_type, target_type,
                    boost_value, expires_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    player_id, source_type, target_type,
                    boost_value, expires_at
                )
            )
            
    def _calculate_level(self, xp: int) -> int:
        """Calculate level from XP amount."""
        level = 1
        xp_table = [0]  # XP for level 1
        for lvl in range(2, 100):
            xp_table.append(
                int(xp_table[-1] + lvl + 300 * (2 ** (lvl / 7.0)))
            )
            if xp >= xp_table[-1]:
                level = lvl
            else:
                break
        return level 