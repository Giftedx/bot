"""Database manager for handling all data storage operations."""

import os
import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    db_path: str
    backup_dir: str
    max_backup_count: int = 5
    auto_backup: bool = True
    
class DatabaseManager:
    """Manages all database operations."""
    
    # SQL statements for table creation
    CREATE_TABLES = {
        "players": """
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                total_playtime INTEGER DEFAULT 0,
                is_member BOOLEAN DEFAULT FALSE,
                member_expires TIMESTAMP
            )
        """,
        
        "player_stats": """
            CREATE TABLE IF NOT EXISTS player_stats (
                player_id INTEGER,
                skill TEXT,
                level INTEGER DEFAULT 1,
                experience REAL DEFAULT 0,
                FOREIGN KEY (player_id) REFERENCES players(id),
                PRIMARY KEY (player_id, skill)
            )
        """,
        
        "player_inventory": """
            CREATE TABLE IF NOT EXISTS player_inventory (
                player_id INTEGER,
                item_id INTEGER,
                quantity INTEGER DEFAULT 0,
                slot INTEGER,
                FOREIGN KEY (player_id) REFERENCES players(id),
                PRIMARY KEY (player_id, slot)
            )
        """,
        
        "player_equipment": """
            CREATE TABLE IF NOT EXISTS player_equipment (
                player_id INTEGER,
                slot TEXT,
                item_id INTEGER,
                FOREIGN KEY (player_id) REFERENCES players(id),
                PRIMARY KEY (player_id, slot)
            )
        """,
        
        "player_bank": """
            CREATE TABLE IF NOT EXISTS player_bank (
                player_id INTEGER,
                tab INTEGER,
                slot INTEGER,
                item_id INTEGER,
                quantity INTEGER DEFAULT 0,
                FOREIGN KEY (player_id) REFERENCES players(id),
                PRIMARY KEY (player_id, tab, slot)
            )
        """,
        
        "player_quests": """
            CREATE TABLE IF NOT EXISTS player_quests (
                player_id INTEGER,
                quest_id INTEGER,
                status TEXT DEFAULT 'not_started',
                progress INTEGER DEFAULT 0,
                completed_at TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id),
                PRIMARY KEY (player_id, quest_id)
            )
        """,
        
        "player_achievements": """
            CREATE TABLE IF NOT EXISTS player_achievements (
                player_id INTEGER,
                achievement_id INTEGER,
                completed_at TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id),
                PRIMARY KEY (player_id, achievement_id)
            )
        """,
        
        "player_locations": """
            CREATE TABLE IF NOT EXISTS player_locations (
                player_id INTEGER,
                x INTEGER,
                y INTEGER,
                plane INTEGER DEFAULT 0,
                region_id INTEGER,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id),
                PRIMARY KEY (player_id)
            )
        """,
        
        "player_friends": """
            CREATE TABLE IF NOT EXISTS player_friends (
                player_id INTEGER,
                friend_id INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id),
                FOREIGN KEY (friend_id) REFERENCES players(id),
                PRIMARY KEY (player_id, friend_id)
            )
        """,
        
        "chat_logs": """
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY,
                player_id INTEGER,
                message TEXT,
                channel TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id) REFERENCES players(id)
            )
        """,
        
        "trade_logs": """
            CREATE TABLE IF NOT EXISTS trade_logs (
                id INTEGER PRIMARY KEY,
                player1_id INTEGER,
                player2_id INTEGER,
                items_given TEXT,
                items_received TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player1_id) REFERENCES players(id),
                FOREIGN KEY (player2_id) REFERENCES players(id)
            )
        """
    }
    
    def __init__(self, config: DatabaseConfig):
        """Initialize database manager.
        
        Args:
            config: Database configuration
        """
        self.config = config
        self.conn = None
        self.cursor = None
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(config.db_path), exist_ok=True)
        os.makedirs(config.backup_dir, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
        
    def _initialize_database(self):
        """Initialize database and create tables."""
        try:
            self.conn = sqlite3.connect(self.config.db_path)
            self.cursor = self.conn.cursor()
            
            # Enable foreign keys
            self.cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create tables
            for table_name, create_sql in self.CREATE_TABLES.items():
                self.cursor.execute(create_sql)
                
            self.conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
            raise
            
    def backup_database(self):
        """Create a backup of the database."""
        if not self.config.auto_backup:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(
            self.config.backup_dir,
            f"backup_{timestamp}.db"
        )
        
        try:
            # Create backup connection
            backup_conn = sqlite3.connect(backup_path)
            
            # Copy database
            with backup_conn:
                self.conn.backup(backup_conn)
                
            # Clean old backups
            self._clean_old_backups()
            
        except sqlite3.Error as e:
            print(f"Error creating backup: {e}")
            raise
            
    def _clean_old_backups(self):
        """Remove old backups exceeding max_backup_count."""
        backups = sorted(
            Path(self.config.backup_dir).glob("backup_*.db"),
            key=os.path.getctime
        )
        
        while len(backups) > self.config.max_backup_count:
            os.remove(backups.pop(0))
            
    def create_player(self, username: str) -> int:
        """Create a new player.
        
        Args:
            username: Player's username
            
        Returns:
            Player ID
        """
        try:
            self.cursor.execute(
                "INSERT INTO players (username) VALUES (?)",
                (username,)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            self.conn.rollback()
            raise
            
    def get_player(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Get player data.
        
        Args:
            player_id: Player's ID
            
        Returns:
            Player data dictionary if found, None otherwise
        """
        try:
            self.cursor.execute(
                "SELECT * FROM players WHERE id = ?",
                (player_id,)
            )
            row = self.cursor.fetchone()
            
            if not row:
                return None
                
            return dict(zip([col[0] for col in self.cursor.description], row))
            
        except sqlite3.Error as e:
            print(f"Error getting player: {e}")
            return None
            
    def update_player_stats(self,
                           player_id: int,
                           skill: str,
                           level: int,
                           experience: float):
        """Update player skill stats.
        
        Args:
            player_id: Player's ID
            skill: Skill name
            level: New level
            experience: New experience amount
        """
        try:
            self.cursor.execute("""
                INSERT INTO player_stats (player_id, skill, level, experience)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(player_id, skill) DO UPDATE SET
                    level = excluded.level,
                    experience = excluded.experience
            """, (player_id, skill, level, experience))
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            self.conn.rollback()
            raise
            
    def update_player_location(self,
                             player_id: int,
                             x: int,
                             y: int,
                             plane: int,
                             region_id: int):
        """Update player location.
        
        Args:
            player_id: Player's ID
            x: X coordinate
            y: Y coordinate
            plane: Plane level
            region_id: Region identifier
        """
        try:
            self.cursor.execute("""
                INSERT INTO player_locations 
                    (player_id, x, y, plane, region_id, last_updated)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(player_id) DO UPDATE SET
                    x = excluded.x,
                    y = excluded.y,
                    plane = excluded.plane,
                    region_id = excluded.region_id,
                    last_updated = CURRENT_TIMESTAMP
            """, (player_id, x, y, plane, region_id))
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            self.conn.rollback()
            raise
            
    def log_chat_message(self,
                        player_id: int,
                        message: str,
                        channel: str):
        """Log a chat message.
        
        Args:
            player_id: Player's ID
            message: Chat message
            channel: Chat channel
        """
        try:
            self.cursor.execute("""
                INSERT INTO chat_logs (player_id, message, channel)
                VALUES (?, ?, ?)
            """, (player_id, message, channel))
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            self.conn.rollback()
            raise
            
    def log_trade(self,
                  player1_id: int,
                  player2_id: int,
                  items_given: Dict[int, int],
                  items_received: Dict[int, int]):
        """Log a trade between players.
        
        Args:
            player1_id: First player's ID
            player2_id: Second player's ID
            items_given: Dictionary of {item_id: quantity} given
            items_received: Dictionary of {item_id: quantity} received
        """
        try:
            self.cursor.execute("""
                INSERT INTO trade_logs 
                    (player1_id, player2_id, items_given, items_received)
                VALUES (?, ?, ?, ?)
            """, (
                player1_id,
                player2_id,
                json.dumps(items_given),
                json.dumps(items_received)
            ))
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            self.conn.rollback()
            raise
            
    def close(self):
        """Close database connection."""
        if self.config.auto_backup:
            self.backup_database()
            
        if self.conn:
            self.conn.close()
            
    def __enter__(self):
        """Context manager enter."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 