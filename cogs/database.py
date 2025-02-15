"""OSRS database manager"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import Equipment, InventoryItem, Player, Skill, SkillType

logger = logging.getLogger(__name__)


class OSRSDatabase:
    """SQLite database manager for OSRS data"""

    def __init__(self, db_path: str = "osrs_bot.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Initialize database tables"""
        with open("cogs/osrs_schema.sql", "r") as f:
            schema = f.read()

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(schema)

    def create_character(self, player: Player) -> bool:
        """Create a new character"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Insert character
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO osrs_characters
                       (user_id, name, created_at, current_world)
                       VALUES (?, ?, ?, ?)""",
                    (player.id, player.name, datetime.now(), 301),
                )
                character_id = cursor.lastrowid

                # Insert default skills
                for skill_type, skill in player.skills.items():
                    cursor.execute(
                        """INSERT INTO osrs_skills
                           (character_id, skill_type, level, xp)
                           VALUES (?, ?, ?, ?)""",
                        (character_id, skill_type.value, skill.level, skill.xp),
                    )

                return True
        except sqlite3.Error as e:
            logger.error(f"Database error creating character: {e}")
            return False

    def load_character(self, user_id: int) -> Optional[Player]:
        """Load character data from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get character data
                cursor.execute(
                    "SELECT id, name FROM osrs_characters WHERE user_id = ?", (user_id,)
                )
                char_data = cursor.fetchone()
                if not char_data:
                    return None

                char_id, name = char_data
                player = Player(id=user_id, name=name)

                # Load skills
                cursor.execute(
                    """SELECT skill_type, level, xp
                       FROM osrs_skills WHERE character_id = ?""",
                    (char_id,),
                )
                for skill_type, level, xp in cursor.fetchall():
                    player.skills[SkillType(skill_type)] = Skill(
                        type=SkillType(skill_type), level=level, xp=xp
                    )

                # Load inventory
                cursor.execute(
                    """SELECT item_id, item_name, quantity, noted
                       FROM osrs_inventory WHERE character_id = ?""",
                    (char_id,),
                )
                for item_id, name, qty, noted in cursor.fetchall():
                    player.inventory.append(
                        InventoryItem(id=item_id, name=name, quantity=qty, noted=noted)
                    )

                # Load equipment
                cursor.execute(
                    """SELECT slot, item_id, item_name
                       FROM osrs_equipment WHERE character_id = ?""",
                    (char_id,),
                )
                equipment = {}
                for slot, item_id, name in cursor.fetchall():
                    equipment[slot] = {"id": item_id, "name": name}
                player.equipment = Equipment(**equipment)

                return player

        except sqlite3.Error as e:
            logger.error(f"Database error loading character: {e}")
            return None

    def update_skills(self, user_id: int, skills: Dict[SkillType, Skill]) -> bool:
        """Update character skills"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM osrs_characters WHERE user_id = ?", (user_id,)
                )
                char_id = cursor.fetchone()[0]

                for skill_type, skill in skills.items():
                    cursor.execute(
                        """UPDATE osrs_skills
                           SET level = ?, xp = ?, last_trained = ?
                           WHERE character_id = ? AND skill_type = ?""",
                        (
                            skill.level,
                            skill.xp,
                            datetime.now(),
                            char_id,
                            skill_type.value,
                        ),
                    )
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error updating skills: {e}")
            return False

    def update_inventory(self, user_id: int, inventory: List[InventoryItem]) -> bool:
        """Update character inventory"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM osrs_characters WHERE user_id = ?", (user_id,)
                )
                char_id = cursor.fetchone()[0]

                # Clear current inventory
                cursor.execute(
                    "DELETE FROM osrs_inventory WHERE character_id = ?", (char_id,)
                )

                # Insert new items
                for item in inventory:
                    cursor.execute(
                        """INSERT INTO osrs_inventory
                           (character_id, item_id, item_name, quantity, noted)
                           VALUES (?, ?, ?, ?, ?)""",
                        (char_id, item.id, item.name, item.quantity, item.noted),
                    )
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error updating inventory: {e}")
            return False

    def update_equipment(self, user_id: int, equipment: Equipment) -> bool:
        """Update character equipment"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM osrs_characters WHERE user_id = ?", (user_id,)
                )
                char_id = cursor.fetchone()[0]

                # Clear current equipment
                cursor.execute(
                    "DELETE FROM osrs_equipment WHERE character_id = ?", (char_id,)
                )

                # Insert equipped items
                for slot, item in equipment.__dict__.items():
                    if item:
                        cursor.execute(
                            """INSERT INTO osrs_equipment
                               (character_id, slot, item_id, item_name)
                               VALUES (?, ?, ?, ?)""",
                            (char_id, slot, item["id"], item["name"]),
                        )
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error updating equipment: {e}")
            return False

    def log_training(
        self, user_id: int, skill_type: SkillType, xp_gained: int, duration: int
    ) -> bool:
        """Log training activity"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM osrs_characters WHERE user_id = ?", (user_id,)
                )
                char_id = cursor.fetchone()[0]

                cursor.execute(
                    """INSERT INTO osrs_training_history
                       (character_id, skill_type, xp_gained, duration)
                       VALUES (?, ?, ?, ?)""",
                    (char_id, skill_type.value, xp_gained, duration),
                )
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error logging training: {e}")
            return False


# Global database instance
osrs_db = OSRSDatabase()
