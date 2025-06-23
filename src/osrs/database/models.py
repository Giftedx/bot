"""SQLite database models for OSRS game data."""
import json
from datetime import datetime
from typing import Dict, List, Optional, cast
import sqlite3
import logging
from dataclasses import dataclass
from enum import Enum

from ..core.constants import SkillType
from ..models.equipment import Equipment, InventoryItem
from ..core.game_math import level_to_xp

logger = logging.getLogger(__name__)


class TransportationType(Enum):
    """Types of transportation methods."""

    SHIP = "ship"
    FERRY = "ferry"
    MINECART = "minecart"
    CANOE = "canoe"
    GNOME_GLIDER = "gnome_glider"
    BALLOON = "balloon"
    SPIRIT_TREE = "spirit_tree"
    CARPET = "carpet"
    QUETZAL = "quetzal"


class TeleportType(Enum):
    """Types of teleportation methods."""

    STANDARD_MAGIC = "standard_magic"
    ANCIENT_MAGIC = "ancient_magic"
    LUNAR_MAGIC = "lunar_magic"
    ARCEUUS_MAGIC = "arceuus_magic"
    JEWELLERY = "jewellery"
    SCROLL = "scroll"
    DIARY = "diary"
    MISC = "misc"


@dataclass
class TransportLocation:
    """Transportation location in the game world."""

    id: int
    name: str
    transport_type: TransportationType
    x: int
    y: int
    plane: int = 0
    members_only: bool = False
    quest_requirement: Optional[str] = None
    achievement_requirement: Optional[str] = None
    destination_x: Optional[int] = None
    destination_y: Optional[int] = None
    destination_plane: Optional[int] = None


@dataclass
class TeleportLocation:
    """Teleportation destination in the game world."""

    id: int
    name: str
    teleport_type: TeleportType
    x: int
    y: int
    plane: int = 0
    level_requirement: Optional[int] = None
    members_only: bool = False
    quest_requirement: Optional[str] = None
    achievement_requirement: Optional[str] = None
    item_requirement: Optional[str] = None


@dataclass
class SpecialLocation:
    """Special location in the game world (fairy rings, obelisks, etc.)."""

    id: int
    name: str
    location_type: str
    x: int
    y: int
    plane: int = 0
    code: Optional[str] = None  # For fairy rings
    members_only: bool = False
    quest_requirement: Optional[str] = None
    achievement_requirement: Optional[str] = None
    level_requirement: Optional[dict] = None  # For skill requirements


class Database:
    """SQLite database manager."""

    def __init__(self, db_path: str = "osrs_bot.db"):
        """Initialize database connection and create tables."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self) -> None:
        """Create necessary database tables if they don't exist."""
        with self.conn:
            # Players table
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY,
                    discord_id INTEGER UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    last_login TIMESTAMP NOT NULL,
                    game_mode TEXT DEFAULT 'normal',
                    world TEXT DEFAULT 'main',
                    gold INTEGER DEFAULT 0
                )
            """
            )

            # Skills table
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY,
                    player_id INTEGER NOT NULL,
                    skill_type TEXT NOT NULL,
                    xp INTEGER DEFAULT 0,
                    FOREIGN KEY (player_id) REFERENCES players (id),
                    UNIQUE (player_id, skill_type)
                )
            """
            )

            # Inventory table
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY,
                    player_id INTEGER NOT NULL,
                    item_data TEXT NOT NULL,
                    FOREIGN KEY (player_id) REFERENCES players (id)
                )
            """
            )

            # Equipment table
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY,
                    player_id INTEGER NOT NULL,
                    slot TEXT NOT NULL,
                    item_data TEXT,
                    FOREIGN KEY (player_id) REFERENCES players (id),
                    UNIQUE (player_id, slot)
                )
            """
            )

            # Bank table
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bank (
                    id INTEGER PRIMARY KEY,
                    player_id INTEGER NOT NULL,
                    item_data TEXT NOT NULL,
                    FOREIGN KEY (player_id) REFERENCES players (id)
                )
            """
            )

            # Transportation table
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS osrs_transportation (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    transport_type TEXT NOT NULL,
                    x INTEGER NOT NULL,
                    y INTEGER NOT NULL,
                    plane INTEGER DEFAULT 0,
                    members_only BOOLEAN DEFAULT FALSE,
                    quest_requirement TEXT,
                    achievement_requirement TEXT,
                    destination_x INTEGER,
                    destination_y INTEGER,
                    destination_plane INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Teleport locations table
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS osrs_teleport_locations (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    teleport_type TEXT NOT NULL,
                    x INTEGER NOT NULL,
                    y INTEGER NOT NULL,
                    plane INTEGER DEFAULT 0,
                    level_requirement INTEGER,
                    members_only BOOLEAN DEFAULT FALSE,
                    quest_requirement TEXT,
                    achievement_requirement TEXT,
                    item_requirement TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Special locations table
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS osrs_special_locations (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    location_type TEXT NOT NULL,
                    x INTEGER NOT NULL,
                    y INTEGER NOT NULL,
                    plane INTEGER DEFAULT 0,
                    code TEXT,
                    members_only BOOLEAN DEFAULT FALSE,
                    quest_requirement TEXT,
                    achievement_requirement TEXT,
                    level_requirement JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

    def create_player(
        self, discord_id: int, name: str, game_mode: str = "normal", world: str = "main"
    ) -> int:
        """
        Create a new player with default skills.

        Args:
            discord_id: Discord user ID
            name: Character name
            game_mode: Game mode (normal, ironman, etc)
            world: World type (main, deadman, etc)

        Returns:
            int: Database ID of created player
        """
        now = datetime.utcnow()

        with self.conn:
            cursor = self.conn.cursor()

            # Create player
            cursor.execute(
                """
                INSERT INTO players (
                    discord_id, name, created_at, last_login,
                    game_mode, world
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (discord_id, name, now, now, game_mode, world),
            )
            player_id = cast(int, cursor.lastrowid)

            # Initialize skills
            for skill in SkillType:
                xp = level_to_xp(10) if skill == SkillType.HITPOINTS else 0
                cursor.execute(
                    """
                    INSERT INTO skills (player_id, skill_type, xp)
                    VALUES (?, ?, ?)
                    """,
                    (player_id, skill.value, xp),
                )

            return player_id

    def get_player(self, discord_id: int) -> Optional[Dict]:
        """Get player data by Discord ID."""
        with self.conn:
            cursor = self.conn.cursor()

            # Get player info
            cursor.execute("SELECT * FROM players WHERE discord_id = ?", (discord_id,))
            player = cursor.fetchone()

            if not player:
                return None

            # Get skills
            cursor.execute("SELECT skill_type, xp FROM skills WHERE player_id = ?", (player["id"],))
            skills = {row["skill_type"]: row["xp"] for row in cursor.fetchall()}

            # Get inventory
            cursor.execute("SELECT item_data FROM inventory WHERE player_id = ?", (player["id"],))
            inventory = [json.loads(row["item_data"]) for row in cursor.fetchall()]

            # Get equipment
            cursor.execute(
                "SELECT slot, item_data FROM equipment WHERE player_id = ?", (player["id"],)
            )
            equipment = {
                row["slot"]: (json.loads(row["item_data"]) if row["item_data"] else None)
                for row in cursor.fetchall()
            }

            return {
                "id": player["id"],
                "discord_id": player["discord_id"],
                "name": player["name"],
                "created_at": player["created_at"],
                "last_login": player["last_login"],
                "game_mode": player["game_mode"],
                "world": player["world"],
                "gold": player["gold"],
                "skills": skills,
                "inventory": inventory,
                "equipment": equipment,
            }

    def update_skills(self, player_id: int, skills: Dict[str, int]) -> None:
        """Update player skill XP."""
        with self.conn:
            cursor = self.conn.cursor()
            for skill_type, xp in skills.items():
                cursor.execute(
                    """
                    UPDATE skills 
                    SET xp = ? 
                    WHERE player_id = ? AND skill_type = ?
                    """,
                    (xp, player_id, skill_type),
                )

    def update_inventory(self, player_id: int, inventory: List[InventoryItem]) -> None:
        """Update player inventory."""
        with self.conn:
            cursor = self.conn.cursor()

            # Clear current inventory
            cursor.execute("DELETE FROM inventory WHERE player_id = ?", (player_id,))

            # Insert new items
            for item in inventory:
                cursor.execute(
                    """
                    INSERT INTO inventory (player_id, item_data)
                    VALUES (?, ?)
                    """,
                    (player_id, json.dumps(item.__dict__)),
                )

    def update_equipment(self, player_id: int, equipment: Equipment) -> None:
        """Update player equipment."""
        with self.conn:
            cursor = self.conn.cursor()

            # Update each equipment slot
            for slot, item in equipment.__dict__.items():
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO equipment (
                        player_id, slot, item_data
                    ) VALUES (?, ?, ?)
                    """,
                    (player_id, slot, json.dumps(item.__dict__) if item else None),
                )

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
