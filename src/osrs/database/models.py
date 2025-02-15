"""SQLite database models for OSRS game data."""
import json
from datetime import datetime
from typing import Dict, List, Optional, cast
import sqlite3
import logging

from src.osrs.models import SkillType, Equipment, InventoryItem
from src.osrs.core.game_math import level_to_xp

logger = logging.getLogger(__name__)


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
            self.conn.execute("""
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
            """)
            
            # Skills table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY,
                    player_id INTEGER NOT NULL,
                    skill_type TEXT NOT NULL,
                    xp INTEGER DEFAULT 0,
                    FOREIGN KEY (player_id) REFERENCES players (id),
                    UNIQUE (player_id, skill_type)
                )
            """)
            
            # Inventory table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY,
                    player_id INTEGER NOT NULL,
                    item_data TEXT NOT NULL,
                    FOREIGN KEY (player_id) REFERENCES players (id)
                )
            """)
            
            # Equipment table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY,
                    player_id INTEGER NOT NULL,
                    slot TEXT NOT NULL,
                    item_data TEXT,
                    FOREIGN KEY (player_id) REFERENCES players (id),
                    UNIQUE (player_id, slot)
                )
            """)
            
            # Bank table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS bank (
                    id INTEGER PRIMARY KEY,
                    player_id INTEGER NOT NULL,
                    item_data TEXT NOT NULL,
                    FOREIGN KEY (player_id) REFERENCES players (id)
                )
            """)

    def create_player(
        self, 
        discord_id: int, 
        name: str,
        game_mode: str = "normal",
        world: str = "main"
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
                (discord_id, name, now, now, game_mode, world)
            )
            player_id = cast(int, cursor.lastrowid)
            
            # Initialize skills
            for skill in SkillType:
                xp = (
                    level_to_xp(10) 
                    if skill == SkillType.HITPOINTS 
                    else 0
                )
                cursor.execute(
                    """
                    INSERT INTO skills (player_id, skill_type, xp)
                    VALUES (?, ?, ?)
                    """,
                    (player_id, skill.value, xp)
                )
            
            return player_id

    def get_player(self, discord_id: int) -> Optional[Dict]:
        """Get player data by Discord ID."""
        with self.conn:
            cursor = self.conn.cursor()
            
            # Get player info
            cursor.execute(
                "SELECT * FROM players WHERE discord_id = ?",
                (discord_id,)
            )
            player = cursor.fetchone()
            
            if not player:
                return None
                
            # Get skills
            cursor.execute(
                "SELECT skill_type, xp FROM skills WHERE player_id = ?",
                (player['id'],)
            )
            skills = {
                row['skill_type']: row['xp'] 
                for row in cursor.fetchall()
            }
            
            # Get inventory
            cursor.execute(
                "SELECT item_data FROM inventory WHERE player_id = ?",
                (player['id'],)
            )
            inventory = [
                json.loads(row['item_data']) 
                for row in cursor.fetchall()
            ]
            
            # Get equipment
            cursor.execute(
                "SELECT slot, item_data FROM equipment WHERE player_id = ?",
                (player['id'],)
            )
            equipment = {
                row['slot']: (
                    json.loads(row['item_data']) 
                    if row['item_data'] 
                    else None
                )
                for row in cursor.fetchall()
            }
            
            return {
                'id': player['id'],
                'discord_id': player['discord_id'],
                'name': player['name'],
                'created_at': player['created_at'],
                'last_login': player['last_login'],
                'game_mode': player['game_mode'],
                'world': player['world'],
                'gold': player['gold'],
                'skills': skills,
                'inventory': inventory,
                'equipment': equipment
            }

    def update_skills(
        self,
        player_id: int,
        skills: Dict[str, int]
    ) -> None:
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
                    (xp, player_id, skill_type)
                )

    def update_inventory(
        self,
        player_id: int,
        inventory: List[InventoryItem]
    ) -> None:
        """Update player inventory."""
        with self.conn:
            cursor = self.conn.cursor()
            
            # Clear current inventory
            cursor.execute(
                "DELETE FROM inventory WHERE player_id = ?",
                (player_id,)
            )
            
            # Insert new items
            for item in inventory:
                cursor.execute(
                    """
                    INSERT INTO inventory (player_id, item_data)
                    VALUES (?, ?)
                    """,
                    (player_id, json.dumps(item.__dict__))
                )

    def update_equipment(
        self,
        player_id: int,
        equipment: Equipment
    ) -> None:
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
                    (
                        player_id,
                        slot,
                        json.dumps(item.__dict__) if item else None
                    )
                )

    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
