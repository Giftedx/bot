import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

from src.core.models.pet import Pet
from src.core.models.player import Player, Skill

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages persistent storage for all system data"""

    def __init__(self, db_path: str = "data/bot.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.setup_database()

    def setup_database(self) -> None:
        """Set up database tables"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # Player data
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                player_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                data JSON NOT NULL,
                last_seen TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        """
        )

        # Pet data
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pets (
                pet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                data JSON NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES players(player_id)
            )
        """
        )

        # Watch history
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS watch_history (
                watch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT NOT NULL,
                content_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                title TEXT NOT NULL,
                duration INTEGER NOT NULL,
                watched_at TIMESTAMP NOT NULL,
                data JSON,
                FOREIGN KEY (player_id) REFERENCES players(player_id)
            )
        """
        )

        # Achievements
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT NOT NULL,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                data JSON NOT NULL,
                unlocked_at TIMESTAMP NOT NULL,
                FOREIGN KEY (player_id) REFERENCES players(player_id)
            )
        """
        )

        # Events
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                data JSON NOT NULL,
                started_at TIMESTAMP NOT NULL,
                ended_at TIMESTAMP,
                active BOOLEAN NOT NULL DEFAULT TRUE
            )
        """
        )

        # Chat logs for roasts
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_logs (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                message TEXT NOT NULL,
                score REAL,
                used_in_roast BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (player_id) REFERENCES players(player_id)
            )
        """
        )

        # Roast history
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS roasts (
                roast_id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                roast_text TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (message_id) REFERENCES chat_logs(message_id)
            )
        """
        )

        # Cross-game effects
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS active_effects (
                effect_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id TEXT NOT NULL,
                type TEXT NOT NULL,
                source TEXT NOT NULL,
                data JSON NOT NULL,
                started_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                FOREIGN KEY (player_id) REFERENCES players(player_id)
            )
        """
        )

        self.conn.commit()

    def save_player(self, player_id: str, username: str, data: Dict[str, Any]) -> None:
        """Save or update player data"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO players (player_id, username, data, last_seen, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(player_id) DO UPDATE SET
                username = excluded.username,
                data = excluded.data,
                last_seen = excluded.last_seen
        """,
            (player_id, username, json.dumps(data), now, now),
        )

        self.conn.commit()

    def get_player(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get player data"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM players WHERE player_id = ?", (player_id,))
        row = cursor.fetchone()

        if row:
            return {
                "player_id": row[0],
                "username": row[1],
                "data": json.loads(row[2]),
                "last_seen": row[3],
                "created_at": row[4],
            }
        return None

    def save_pet(self, pet: Pet) -> None:
        """Save or update pet data"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        pet_data = pet.to_dict()

        # The unique id is not part of the JSON blob
        pet_data.pop("id", None)

        if pet.pet_id:
            # Update existing pet
            cursor.execute(
                """
                UPDATE pets 
                SET owner_id = ?, name = ?, type = ?, data = ?
                WHERE pet_id = ?
            """,
                (pet.owner_id, pet.name, pet.origin.value, json.dumps(pet_data), pet.pet_id),
            )
        else:
            # Insert new pet
            cursor.execute(
                """
                INSERT INTO pets (owner_id, name, type, data, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (pet.owner_id, pet.name, pet.origin.value, json.dumps(pet_data), now),
            )
            pet.pet_id = cursor.lastrowid

        self.conn.commit()

    def get_player_pets(self, player_id: str) -> List[Pet]:
        """Get all pets for a player"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT pet_id, owner_id, name, type, data, created_at FROM pets WHERE owner_id = ?",
            (player_id,),
        )

        rows = cursor.fetchall()
        pets = []
        for row in rows:
            row_dict = {
                "pet_id": row[0],
                "owner_id": row[1],
                "name": row[2],
                "type": row[3],
                "data": json.loads(row[4]),
                "created_at": row[5],
            }
            pets.append(Pet.from_db_row(row_dict))
        return pets

    def add_watch_record(self, player_id: str, content_data: Dict[str, Any]) -> None:
        """Add a watch history record"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO watch_history (
                player_id, content_id, content_type, title,
                duration, watched_at, data
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                player_id,
                content_data["id"],
                content_data["type"],
                content_data["title"],
                content_data.get("duration", 0),
                now,
                json.dumps(content_data),
            ),
        )

        self.conn.commit()

    def get_watch_history(self, player_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get watch history for a player"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM watch_history 
            WHERE player_id = ? 
            ORDER BY watched_at DESC 
            LIMIT ?
        """,
            (player_id, limit),
        )

        return [
            {
                "watch_id": row[0],
                "player_id": row[1],
                "content_id": row[2],
                "content_type": row[3],
                "title": row[4],
                "duration": row[5],
                "watched_at": row[6],
                "data": json.loads(row[7]) if row[7] else None,
            }
            for row in cursor.fetchall()
        ]

    def unlock_achievement(
        self, player_id: str, achievement_type: str, name: str, data: Dict[str, Any]
    ) -> None:
        """Record an achievement unlock"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO achievements (
                player_id, type, name, data, unlocked_at
            ) VALUES (?, ?, ?, ?, ?)
        """,
            (player_id, achievement_type, name, json.dumps(data), now),
        )

        self.conn.commit()

    def get_player_achievements(self, player_id: str) -> List[Dict[str, Any]]:
        """Get all achievements for a player"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM achievements WHERE player_id = ?", (player_id,))

        return [
            {
                "achievement_id": row[0],
                "player_id": row[1],
                "type": row[2],
                "name": row[3],
                "data": json.loads(row[4]),
                "unlocked_at": row[5],
            }
            for row in cursor.fetchall()
        ]

    def start_event(self, event_type: str, data: Dict[str, Any]) -> int:
        """Start a new event"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO events (type, status, data, started_at, active)
            VALUES (?, 'started', ?, ?, TRUE)
            RETURNING event_id
        """,
            (event_type, json.dumps(data), now),
        )

        event_id = cursor.fetchone()[0]
        self.conn.commit()
        return event_id

    def end_event(self, event_id: int) -> None:
        """End an active event"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            UPDATE events 
            SET status = 'ended', ended_at = ?, active = FALSE
            WHERE event_id = ?
        """,
            (now, event_id),
        )

        self.conn.commit()

    def get_active_events(self) -> List[Dict[str, Any]]:
        """Get all currently active events"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM events WHERE active = TRUE")

        return [
            {
                "event_id": row[0],
                "type": row[1],
                "status": row[2],
                "data": json.loads(row[3]),
                "started_at": row[4],
                "ended_at": row[5],
                "active": row[6],
            }
            for row in cursor.fetchall()
        ]

    def log_chat_message(
        self, player_id: str, channel_id: str, message: str, score: Optional[float] = None
    ) -> int:
        """Log a chat message for potential roasts"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO chat_logs (
                player_id, channel_id, message, score, created_at
            ) VALUES (?, ?, ?, ?, ?)
            RETURNING message_id
        """,
            (player_id, channel_id, message, score, now),
        )

        message_id = cursor.fetchone()[0]
        self.conn.commit()
        return message_id

    def add_roast(self, message_id: int, roast_text: str) -> None:
        """Record a roast for a message"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO roasts (message_id, roast_text, created_at)
            VALUES (?, ?, ?)
        """,
            (message_id, roast_text, now),
        )

        cursor.execute(
            """
            UPDATE chat_logs 
            SET used_in_roast = TRUE 
            WHERE message_id = ?
        """,
            (message_id,),
        )

        self.conn.commit()

    def get_roastable_messages(
        self, min_score: float = 0.5, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get messages that could be roasted"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM chat_logs 
            WHERE score >= ? AND used_in_roast = FALSE
            ORDER BY score DESC 
            LIMIT ?
        """,
            (min_score, limit),
        )

        return [
            {
                "message_id": row[0],
                "player_id": row[1],
                "channel_id": row[2],
                "message": row[3],
                "score": row[4],
                "used_in_roast": row[5],
                "created_at": row[6],
            }
            for row in cursor.fetchall()
        ]

    def add_effect(
        self,
        player_id: str,
        effect_type: str,
        source: str,
        data: Dict[str, Any],
        duration_seconds: Optional[int] = None,
    ) -> None:
        """Add an active effect for a player"""
        cursor = self.conn.cursor()
        now = datetime.now()
        started_at = now.isoformat()
        expires_at = (
            (now + timedelta(seconds=duration_seconds)).isoformat() if duration_seconds else None
        )

        cursor.execute(
            """
            INSERT INTO active_effects (
                player_id, type, source, data, started_at, expires_at, active
            ) VALUES (?, ?, ?, ?, ?, ?, TRUE)
        """,
            (player_id, effect_type, source, json.dumps(data), started_at, expires_at),
        )

        self.conn.commit()

    def get_active_effects(self, player_id: str) -> List[Dict[str, Any]]:
        """Get all active effects for a player"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            SELECT * FROM active_effects 
            WHERE player_id = ? 
            AND active = TRUE 
            AND (expires_at IS NULL OR expires_at > ?)
        """,
            (player_id, now),
        )

        return [
            {
                "effect_id": row[0],
                "player_id": row[1],
                "type": row[2],
                "source": row[3],
                "data": json.loads(row[4]),
                "started_at": row[5],
                "expires_at": row[6],
                "active": row[7],
            }
            for row in cursor.fetchall()
        ]

    def cleanup_expired_effects(self) -> None:
        """Clean up expired effects"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute(
            """
            UPDATE active_effects 
            SET active = FALSE 
            WHERE active = TRUE 
            AND expires_at IS NOT NULL 
            AND expires_at <= ?
        """,
            (now,),
        )

        self.conn.commit()

    def close(self) -> None:
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_top_achievement_points(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top players by achievement points"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT player_id, COUNT(*) as achievement_count,
                   SUM(CAST(json_extract(data, '$.points') AS INTEGER)) as achievement_points
            FROM achievements
            GROUP BY player_id
            ORDER BY achievement_points DESC
            LIMIT ?
        """,
            (limit,),
        )

        return [
            {"player_id": row[0], "achievement_count": row[1], "achievement_points": row[2]}
            for row in cursor.fetchall()
        ]

    def get_top_pet_counts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top players by number of pets"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT owner_id as player_id, COUNT(*) as pet_count
            FROM pets
            GROUP BY owner_id
            ORDER BY pet_count DESC
            LIMIT ?
        """,
            (limit,),
        )

        return [{"player_id": row[0], "pet_count": row[1]} for row in cursor.fetchall()]

    def get_top_watch_times(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top players by watch time"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT player_id, COUNT(*) as watch_count,
                   SUM(duration) as total_duration
            FROM watch_history
            GROUP BY player_id
            ORDER BY total_duration DESC
            LIMIT ?
        """,
            (limit,),
        )

        return [
            {
                "player_id": row[0],
                "watch_count": row[1],
                "watch_time": row[2] / 3600,  # Convert seconds to hours
            }
            for row in cursor.fetchall()
        ]

    def get_top_roast_scores(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top players by average roast score"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT player_id, COUNT(*) as roast_count,
                   AVG(score) as avg_score,
                   MAX(score) as max_score
            FROM chat_logs
            WHERE used_in_roast = TRUE
            GROUP BY player_id
            HAVING roast_count >= 5
            ORDER BY avg_score DESC
            LIMIT ?
        """,
            (limit,),
        )

        return [
            {"player_id": row[0], "roast_count": row[1], "avg_score": row[2], "max_score": row[3]}
            for row in cursor.fetchall()
        ]

    def get_top_event_participants(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top players by event participation"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT player_id, COUNT(*) as event_count,
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count
            FROM events
            GROUP BY player_id
            ORDER BY event_count DESC
            LIMIT ?
        """,
            (limit,),
        )

        return [
            {"player_id": row[0], "event_count": row[1], "completed_count": row[2]}
            for row in cursor.fetchall()
        ]

    def get_top_effect_counts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top players by active effects"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT player_id, COUNT(*) as effect_count,
                   COUNT(CASE WHEN expires_at IS NULL THEN 1 END) as permanent_count
            FROM active_effects
            WHERE active = TRUE
            GROUP BY player_id
            ORDER BY effect_count DESC
            LIMIT ?
        """,
            (limit,),
        )

        return [
            {"player_id": row[0], "effect_count": row[1], "permanent_count": row[2]}
            for row in cursor.fetchall()
        ]

    def get_player_roasts(self, player_id: str) -> List[Dict[str, Any]]:
        """Get all roasts for a player"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT m.*, r.roast_text, r.created_at as roast_at
            FROM chat_logs m
            JOIN roasts r ON r.message_id = m.message_id
            WHERE m.player_id = ?
            ORDER BY r.created_at DESC
        """,
            (player_id,),
        )

        return [
            {
                "message_id": row[0],
                "player_id": row[1],
                "channel_id": row[2],
                "message": row[3],
                "score": row[4],
                "used_in_roast": bool(row[5]),
                "created_at": row[6],
                "roast_text": row[7],
                "roast_at": row[8],
            }
            for row in cursor.fetchall()
        ]

    def get_player_events(self, player_id: str) -> List[Dict[str, Any]]:
        """Get all events a player participated in"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT e.*, p.role, p.joined_at
            FROM events e
            JOIN event_participants p ON p.event_id = e.event_id
            WHERE p.player_id = ?
            ORDER BY e.started_at DESC
        """,
            (player_id,),
        )

        return [
            {
                "event_id": row[0],
                "type": row[1],
                "status": row[2],
                "data": json.loads(row[3]),
                "started_at": row[4],
                "ended_at": row[5],
                "active": bool(row[6]),
                "role": row[7],
                "joined_at": row[8],
            }
            for row in cursor.fetchall()
        ]

    def get_effect(self, effect_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific effect"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM active_effects
            WHERE effect_id = ?
        """,
            (effect_id,),
        )

        row = cursor.fetchone()
        if row:
            return {
                "effect_id": row[0],
                "player_id": row[1],
                "type": row[2],
                "source": row[3],
                "data": json.loads(row[4]),
                "started_at": row[5],
                "expires_at": row[6],
                "active": bool(row[7]),
            }
        return None

    def remove_effect(self, effect_id: int) -> None:
        """Remove an effect"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE active_effects
            SET active = FALSE
            WHERE effect_id = ?
        """,
            (effect_id,),
        )

        self.conn.commit()

    def clear_effects(self, player_id: str) -> int:
        """Clear all effects for a player. Returns number of effects cleared."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE active_effects
            SET active = FALSE
            WHERE player_id = ? AND active = TRUE
        """,
            (player_id,),
        )

        count = cursor.rowcount
        self.conn.commit()
        return count

    def create_player(self, player_id: int, username: str) -> Player:
        """Create a new player and save them to the database."""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        # Default skills for a new player
        default_skills = {
            "attack": Skill(),
            "strength": Skill(),
            "defence": Skill(),
            "hitpoints": Skill(level=10, xp=1154),
            "ranged": Skill(),
            "magic": Skill(),
            "prayer": Skill(),
        }

        new_player = Player(user_id=player_id, username=username, skills=default_skills)

        player_data = new_player.to_dict()

        cursor.execute(
            "INSERT INTO players (player_id, username, data, last_seen, created_at) VALUES (?, ?, ?, ?, ?)",
            (player_id, username, json.dumps(player_data), now, now),
        )
        self.conn.commit()
        return new_player

    def save_player(self, player: Player) -> None:
        """Save or update a player's data."""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()

        player_data = player.to_dict()

        cursor.execute(
            "UPDATE players SET data = ?, last_seen = ? WHERE player_id = ?",
            (json.dumps(player_data), now, player.user_id),
        )
        self.conn.commit()

    def get_player_by_name(self, username: str) -> Optional[Dict[str, Any]]:
        """Retrieve a player by their username."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM players WHERE username = ?", (username,))
        row = cursor.fetchone()

        if row:
            return {
                "player_id": row[0],
                "username": row[1],
                "data": json.loads(row[2]),
                "last_seen": row[3],
                "created_at": row[4],
            }
        return None
