"""Unified database manager for the Discord bot.

This module provides a centralized database management system that combines
the functionality from all existing database managers into a cohesive,
maintainable solution.
"""

import logging
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic
from datetime import datetime, timedelta
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

from .exceptions import DatabaseError
from ..database.models import Player
from ..bot.pets.models import Pet, PetType

logger = logging.getLogger(__name__)

# Sentinel value for distinguishing between None and "not found"
_SENTINEL = object()

T = TypeVar("T")


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    db_path: str = "data/bot.db"
    backup_dir: str = "data/backups"
    max_backup_count: int = 10
    auto_backup: bool = True
    backup_interval_hours: int = 24
    connection_timeout: int = 30
    enable_wal_mode: bool = True
    enable_foreign_keys: bool = True


class DatabaseRepository(Generic[T], ABC):
    """Abstract base repository for database operations."""

    def __init__(self, db_manager: "UnifiedDatabaseManager"):
        self.db = db_manager

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    def get_by_id(self, entity_id: Union[int, str]) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    def update(self, entity: T) -> T:
        """Update an entity."""
        pass

    @abstractmethod
    def delete(self, entity_id: Union[int, str]) -> bool:
        """Delete an entity."""
        pass


class PlayerRepository(DatabaseRepository[Player]):
    """Repository for player-related operations."""

    def create(self, player: Player) -> Player:
        """Create a new player."""
        with self.db.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO players (discord_id, username, data, created_at, last_seen)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    player.discord_id,
                    player.username,
                    json.dumps(asdict(player)),
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )
            player.id = cursor.lastrowid
            return player

    def get_by_id(self, player_id: Union[int, str]) -> Optional[Player]:
        """Get player by ID."""
        with self.db.get_cursor() as cursor:
            if isinstance(player_id, str):
                # Assume it's a discord_id
                cursor.execute("SELECT * FROM players WHERE discord_id = ?", (int(player_id),))
            else:
                cursor.execute("SELECT * FROM players WHERE id = ?", (player_id,))

            row = cursor.fetchone()
            if row:
                data = json.loads(row["data"]) if row["data"] else {}
                return Player(
                    id=row["id"], discord_id=row["discord_id"], username=row["username"], **data
                )
            return None

    def get_by_discord_id(self, discord_id: int) -> Optional[Player]:
        """Get player by Discord ID."""
        return self.get_by_id(str(discord_id))

    def update(self, player: Player) -> Player:
        """Update a player."""
        with self.db.transaction() as cursor:
            cursor.execute(
                """
                UPDATE players 
                SET username = ?, data = ?, last_seen = ?
                WHERE id = ?
                """,
                (
                    player.username,
                    json.dumps(asdict(player)),
                    datetime.now().isoformat(),
                    player.id,
                ),
            )
            return player

    def delete(self, player_id: Union[int, str]) -> bool:
        """Delete a player."""
        with self.db.transaction() as cursor:
            cursor.execute("DELETE FROM players WHERE id = ?", (player_id,))
            return cursor.rowcount > 0


class PetRepository(DatabaseRepository[Pet]):
    """Repository for pet-related operations."""

    def create(self, pet: Pet) -> Pet:
        """Create a new pet."""
        with self.db.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO pets (owner_id, name, type, data, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    pet.owner_id,
                    pet.name,
                    pet.element.value,  # Use element instead of type
                    json.dumps({
                        "element": pet.element.value,
                        "level": pet.level,
                        "experience": pet.experience,
                        "max_hp": pet.max_hp,
                        "base_damage": pet.base_damage,
                        "moves": pet.moves
                    }),
                    datetime.now().isoformat(),
                ),
            )
            pet.id = cursor.lastrowid  # Use 'id' field from Pet model
            return pet

    def get_by_id(self, pet_id: Union[int, str]) -> Optional[Pet]:
        """Get pet by ID."""
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM pets WHERE pet_id = ?", (pet_id,))
            row = cursor.fetchone()
            if row:
                data = json.loads(row["data"]) if row["data"] else {}
                return Pet(
                    id=row["pet_id"],  # Map pet_id to id
                    name=row["name"],
                    owner_id=row["owner_id"],
                    element=PetType(data.get("element", "FIRE")),
                    level=data.get("level", 1),
                    experience=data.get("experience", 0),
                    max_hp=data.get("max_hp", 100),
                    base_damage=data.get("base_damage", 10),
                    moves=data.get("moves", [])
                )
            return None

    def get_by_owner(self, owner_id: int) -> List[Pet]:
        """Get all pets for an owner."""
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM pets WHERE owner_id = ?", (owner_id,))
            rows = cursor.fetchall()
            pets = []
            for row in rows:
                data = json.loads(row["data"]) if row["data"] else {}
                pet = Pet(
                    id=row["pet_id"],  # Map pet_id to id
                    name=row["name"],
                    owner_id=row["owner_id"],
                    element=PetType(data.get("element", "FIRE")),
                    level=data.get("level", 1),
                    experience=data.get("experience", 0),
                    max_hp=data.get("max_hp", 100),
                    base_damage=data.get("base_damage", 10),
                    moves=data.get("moves", [])
                )
                pets.append(pet)
            return pets

    def update(self, pet: Pet) -> Pet:
        """Update a pet."""
        with self.db.transaction() as cursor:
            pet_data = {
                "element": pet.element.value,
                "level": pet.level,
                "experience": pet.experience,
                "max_hp": pet.max_hp,
                "base_damage": pet.base_damage,
                "moves": pet.moves
            }
            cursor.execute(
                """
                UPDATE pets 
                SET name = ?, data = ?
                WHERE pet_id = ?
                """,
                (pet.name, json.dumps(pet_data), pet.id),  # Use pet.id (maps to pet_id in DB)
            )
            return pet

    def delete(self, pet_id: Union[int, str]) -> bool:
        """Delete a pet."""
        with self.db.transaction() as cursor:
            cursor.execute("DELETE FROM pets WHERE pet_id = ?", (pet_id,))
            return cursor.rowcount > 0


class TriviaRepository:
    """Repository for trivia score operations."""

    def __init__(self, db_manager: "UnifiedDatabaseManager"):
        self.db = db_manager

    def increment_score(self, player_id: int, amount: int = 1) -> int:
        """Increments a player's trivia score, returning the new score."""
        with self.db.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO trivia_scores (player_id, score)
                VALUES (?, ?)
                ON CONFLICT(player_id) DO UPDATE SET score = score + excluded.score;
                """,
                (player_id, amount),
            )
            cursor.execute("SELECT score FROM trivia_scores WHERE player_id = ?", (player_id,))
            new_score = cursor.fetchone()
            return new_score[0] if new_score else amount

    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Gets the top trivia scores."""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT p.username, ts.score
                FROM trivia_scores ts
                JOIN players p ON ts.player_id = p.discord_id
                ORDER BY ts.score DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [{"username": row[0], "score": row[1]} for row in cursor.fetchall()]


class UnifiedDatabaseManager:
    """Unified database manager combining all bot functionality."""

    # Schema definitions
    SCHEMA = {
        "players": """
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id INTEGER UNIQUE NOT NULL,
                username TEXT NOT NULL,
                data JSON,
                created_at TIMESTAMP NOT NULL,
                last_seen TIMESTAMP NOT NULL
            )
        """,
        "pets": """
            CREATE TABLE IF NOT EXISTS pets (
                pet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                data JSON NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES players(discord_id)
            )
        """,
        "player_stats": """
            CREATE TABLE IF NOT EXISTS player_stats (
                player_id INTEGER PRIMARY KEY,
                skill_data JSON NOT NULL,
                combat_data JSON,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        """,
        "inventory": """
            CREATE TABLE IF NOT EXISTS inventory (
                player_id INTEGER,
                slot INTEGER,
                item_id INTEGER,
                quantity INTEGER DEFAULT 0,
                item_data JSON,
                PRIMARY KEY (player_id, slot),
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        """,
        "equipment": """
            CREATE TABLE IF NOT EXISTS equipment (
                player_id INTEGER,
                slot TEXT,
                item_id INTEGER,
                item_data JSON,
                PRIMARY KEY (player_id, slot),
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        """,
        "bank": """
            CREATE TABLE IF NOT EXISTS bank (
                player_id INTEGER,
                tab INTEGER DEFAULT 0,
                slot INTEGER,
                item_id INTEGER,
                quantity INTEGER DEFAULT 0,
                item_data JSON,
                PRIMARY KEY (player_id, tab, slot),
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        """,
        "achievements": """
            CREATE TABLE IF NOT EXISTS achievements (
                achievement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                data JSON NOT NULL,
                unlocked_at TIMESTAMP NOT NULL,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        """,
        "events": """
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                data JSON NOT NULL,
                started_at TIMESTAMP NOT NULL,
                ended_at TIMESTAMP,
                active BOOLEAN NOT NULL DEFAULT TRUE
            )
        """,
        "active_effects": """
            CREATE TABLE IF NOT EXISTS active_effects (
                effect_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                source TEXT NOT NULL,
                data JSON NOT NULL,
                started_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        """,
        "watch_history": """
            CREATE TABLE IF NOT EXISTS watch_history (
                watch_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                content_id TEXT NOT NULL,
                content_type TEXT NOT NULL,
                title TEXT NOT NULL,
                duration INTEGER NOT NULL,
                watched_at TIMESTAMP NOT NULL,
                data JSON,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        """,
        "chat_logs": """
            CREATE TABLE IF NOT EXISTS chat_logs (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                channel_id TEXT NOT NULL,
                message TEXT NOT NULL,
                score REAL,
                used_in_roast BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        """,
        "roasts": """
            CREATE TABLE IF NOT EXISTS roasts (
                roast_id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                roast_text TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (message_id) REFERENCES chat_logs(message_id)
            )
        """,
        "combat_logs": """
            CREATE TABLE IF NOT EXISTS combat_logs (
                combat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                opponent_type TEXT NOT NULL,
                opponent_id INTEGER,
                winner_id INTEGER,
                total_damage_dealt INTEGER DEFAULT 0,
                total_damage_taken INTEGER DEFAULT 0,
                experience_gained REAL DEFAULT 0,
                drops JSON,
                started_at TIMESTAMP NOT NULL,
                ended_at TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        """,
        "combat_hits": """
            CREATE TABLE IF NOT EXISTS combat_hits (
                hit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                combat_id INTEGER NOT NULL,
                attacker_id INTEGER NOT NULL,
                defender_id INTEGER NOT NULL,
                damage INTEGER NOT NULL,
                hit_type TEXT NOT NULL,
                accuracy REAL NOT NULL,
                max_hit INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (combat_id) REFERENCES combat_logs(combat_id),
                FOREIGN KEY (attacker_id) REFERENCES players(id),
                FOREIGN KEY (defender_id) REFERENCES players(id)
            )
        """,
        "trivia_scores": """
            CREATE TABLE IF NOT EXISTS trivia_scores (
                player_id INTEGER PRIMARY KEY,
                score INTEGER NOT NULL DEFAULT 0
            )
        """,
    }

    def __init__(self, config: Optional[DatabaseConfig] = None):
        """Initialize the unified database manager."""
        self.config = config or DatabaseConfig()
        self.db_path = Path(self.config.db_path)
        self.backup_dir = Path(self.config.backup_dir)

        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self._connection = None
        self._last_backup = None

        # Initialize repositories
        self.players = PlayerRepository(self)
        self.pets = PetRepository(self)
        self.trivia = TriviaRepository(self)

        # Initialize database
        self._initialize_database()

        logger.info(f"UnifiedDatabaseManager initialized with database at {self.db_path}")

        # --- Convenience helpers for legacy cogs migrated to unified system ---

    # ---------------------------------------------------------------------
    # Watch history helpers
    # ---------------------------------------------------------------------

    def add_watch_record(self, player_id: int, record: Dict[str, Any]) -> bool:
        """Insert a watch history record.

        Parameters
        ----------
        player_id: int
            Discord user ID of the viewer.
        record: Dict[str, Any]
            Arbitrary metadata about the watch session. Must include at least:
                id (str): content identifier (e.g. party id)
                type (str): content type (e.g. 'group_watch')
                title (str): human-readable title
                started_at (str): ISO timestamp when viewing began
            Extra keys will be stored in the JSON `data` column.
        """
        try:
            with self.transaction() as cursor:
                cursor.execute(
                    """
                    INSERT INTO watch_history (player_id, content_id, content_type, title, duration, watched_at, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        player_id,
                        record.get("id"),
                        record.get("type", "unknown"),
                        record.get("title", "unknown"),
                        record.get("duration", 0),
                        record.get("started_at", datetime.now().isoformat()),
                        json.dumps(record),
                    ),
                )
            return True
        except Exception as e:
            logger.error(f"Failed to add watch record: {e}")
            return False

    def get_watch_history(self, player_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent watch history for a user."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM watch_history WHERE player_id = ? ORDER BY watched_at DESC LIMIT ?
                    """,
                    (player_id, limit),
                )
                rows = cursor.fetchall()
            history = []
            for row in rows:
                rec = dict(row)
                if isinstance(rec.get("data"), str):
                    try:
                        rec["data"] = json.loads(rec["data"])
                    except Exception:
                        rec["data"] = {}
                history.append(rec)
            return history
        except Exception as e:
            logger.error(f"Failed to get watch history: {e}")
            return []

    # ---------------------------------------------------------------------
    # Active effects helpers
    # ---------------------------------------------------------------------

    def get_active_effects(self, player_id: int) -> List[Dict[str, Any]]:
        """Return all currently active effects for a player."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM active_effects WHERE player_id = ? AND active = 1
                    """,
                    (player_id,),
                )
                rows = cursor.fetchall()
            results = []
            for row in rows:
                record = dict(row)
                # Ensure JSON fields are decoded
                if isinstance(record.get("data"), str):
                    try:
                        record["data"] = json.loads(record["data"])
                    except Exception:
                        record["data"] = {}
                results.append(record)
            return results
        except Exception as e:
            logger.error(f"Failed to fetch active effects: {e}")
            return []

    def get_effect(self, effect_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single effect by its ID."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT * FROM active_effects WHERE effect_id = ?", (effect_id,))
                row = cursor.fetchone()
            if not row:
                return None
            record = dict(row)
            if isinstance(record.get("data"), str):
                try:
                    record["data"] = json.loads(record["data"])
                except Exception:
                    record["data"] = {}
            return record
        except Exception as e:
            logger.error(f"Failed to get effect: {e}")
            return None

    def remove_effect(self, effect_id: int) -> bool:
        """Mark an effect as inactive (soft delete)."""
        try:
            with self.transaction() as cursor:
                cursor.execute(
                    """
                    UPDATE active_effects SET active = 0 WHERE effect_id = ?
                    """,
                    (effect_id,),
                )
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to remove effect: {e}")
            return False

    def clear_effects(self, player_id: int) -> int:
        """Deactivate all effects for a given player. Returns number of effects cleared."""
        try:
            with self.transaction() as cursor:
                cursor.execute(
                    """
                    UPDATE active_effects SET active = 0 WHERE player_id = ? AND active = 1
                    """,
                    (player_id,),
                )
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Failed to clear effects: {e}")
            return 0

    def add_effect(
        self,
        player_id: int,
        effect_type: str,
        source: str,
        data: Dict[str, Any],
        duration_seconds: Optional[int] = None,
    ) -> int:
        """Insert a new effect and return its generated ID."""
        try:
            expires_at = (
                (datetime.now() + timedelta(seconds=duration_seconds)).isoformat()
                if duration_seconds
                else None
            )
            with self.transaction() as cursor:
                cursor.execute(
                    """
                    INSERT INTO active_effects (player_id, type, source, data, started_at, expires_at, active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                    """,
                    (
                        player_id,
                        effect_type,
                        source,
                        json.dumps(data),
                        datetime.now().isoformat(),
                        expires_at,
                    ),
                )
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to add effect: {e}")
            return -1

    # ---------------------------------------------------------------------
    # Pet helpers (legacy compatibility)
    # ---------------------------------------------------------------------

    def get_player_pets(self, owner_id: str) -> List[Dict[str, Any]]:
        """Return list of pets owned by a Discord user."""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT * FROM pets WHERE owner_id = ?", (owner_id,))
                rows = cursor.fetchall()
            pets = []
            for row in rows:
                record = dict(row)
                # Decode JSON data
                if isinstance(record.get("data"), str):
                    try:
                        record["data"] = json.loads(record["data"])
                    except Exception:
                        record["data"] = {}
                pets.append(record)
            return pets
        except Exception as e:
            logger.error(f"Failed to fetch pets: {e}")
            return []

    def save_pet(self, pet: Dict[str, Any]) -> bool:
        """Insert or update pet record based on presence of pet_id."""
        try:
            with self.transaction() as cursor:
                if pet.get("pet_id"):
                    cursor.execute(
                        """
                        UPDATE pets
                        SET name = ?, type = ?, data = ?
                        WHERE pet_id = ?
                        """,
                        (
                            pet.get("name"),
                            pet.get("type"),
                            json.dumps(pet.get("data", {})),
                            pet["pet_id"],
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO pets (owner_id, name, type, data, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            pet.get("owner_id"),
                            pet.get("name"),
                            pet.get("type"),
                            json.dumps(pet.get("data", {})),
                            datetime.now().isoformat(),
                        ),
                    )
                    pet["pet_id"] = cursor.lastrowid
            return True
        except Exception as e:
            logger.error(f"Failed to save pet: {e}")
            return False

    def _initialize_database(self) -> None:
        """Initialize database with schema."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Configure SQLite
                if self.config.enable_foreign_keys:
                    cursor.execute("PRAGMA foreign_keys = ON")

                if self.config.enable_wal_mode:
                    cursor.execute("PRAGMA journal_mode = WAL")

                cursor.execute("PRAGMA synchronous = NORMAL")
                cursor.execute(f"PRAGMA busy_timeout = {self.config.connection_timeout * 1000}")

                # Create all tables
                for table_name, schema_sql in self.SCHEMA.items():
                    cursor.execute(schema_sql)
                    logger.debug(f"Created/verified table: {table_name}")

                conn.commit()
                logger.info("Database schema initialized successfully")

        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

    @contextmanager
    def get_connection(self):
        """Get a database connection with proper error handling."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=self.config.connection_timeout)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_cursor(self):
        """Get a database cursor for read operations."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            except sqlite3.Error as e:
                logger.error(f"Database cursor error: {e}")
                raise DatabaseError(f"Database query failed: {e}")

    @contextmanager
    def transaction(self):
        """Get a database cursor with transaction management."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                logger.error(f"Transaction error: {e}")
                raise DatabaseError(f"Transaction failed: {e}")

    def backup_database(self) -> bool:
        """Create a backup of the database."""
        if not self.config.auto_backup:
            return False

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}.db"

            with self.get_connection() as source_conn:
                backup_conn = sqlite3.connect(backup_path)
                source_conn.backup(backup_conn)
                backup_conn.close()

            self._last_backup = datetime.now()
            self._cleanup_old_backups()

            logger.info(f"Database backed up to {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False

    def _cleanup_old_backups(self) -> None:
        """Remove old backup files."""
        try:
            backup_files = list(self.backup_dir.glob("backup_*.db"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Keep only the most recent backups
            for old_backup in backup_files[self.config.max_backup_count :]:
                old_backup.unlink()
                logger.debug(f"Removed old backup: {old_backup}")

        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")

    def should_backup(self) -> bool:
        """Check if a backup should be performed."""
        if not self.config.auto_backup:
            return False

        if self._last_backup is None:
            return True

        time_since_backup = datetime.now() - self._last_backup
        return time_since_backup.total_seconds() >= (self.config.backup_interval_hours * 3600)

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        stats = {}

        try:
            with self.get_cursor() as cursor:
                # Get table counts
                for table_name in self.SCHEMA.keys():
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    stats[f"{table_name}_count"] = cursor.fetchone()[0]

                # Get database size
                stats["database_size_bytes"] = self.db_path.stat().st_size
                stats["database_path"] = str(self.db_path)
                stats["last_backup"] = self._last_backup.isoformat() if self._last_backup else None

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            stats["error"] = str(e)

        return stats

    def close(self) -> None:
        """Close database connections and cleanup."""
        try:
            if self.should_backup():
                self.backup_database()
            logger.info("Database manager closed successfully")
        except Exception as e:
            logger.error(f"Error closing database manager: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
